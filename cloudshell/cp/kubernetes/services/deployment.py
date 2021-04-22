import time
from multiprocessing import TimeoutError

from kubernetes.client import (
    V1Container,
    V1ContainerPort,
    V1DeleteOptions,
    V1Deployment,
    V1DeploymentSpec,
    V1EnvVar,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
)
from kubernetes.client.rest import ApiException

from cloudshell.cp.kubernetes.services.tags import TagsService


class KubernetesDeploymentService:
    def __init__(self, logger, clients, cancellation_manager):
        """Init.

        :param logging.Logger logger:
        :param cloudshell.cp.kubernetes.models.clients.
            KubernetesClients clients:
        """
        self._logger = logger
        self._clients = clients
        self.cancellation_manager = cancellation_manager

    def delete_app(self, namespace, app_name_to_delete):
        """Delete App.

        Delete a deployment immediately. All pods are deleted in the foreground.
        :param str namespace:
        :param str app_name_to_delete:
        :return:
        """
        try:
            delete_options = V1DeleteOptions(
                propagation_policy="Foreground", grace_period_seconds=0
            )
            self._clients.apps_api.delete_namespaced_deployment(
                name=app_name_to_delete,
                namespace=namespace,
                body=delete_options,
                pretty="true",
            )
        except ApiException as e:
            if e.status == 404:
                # Deployment does not exist, nothing to delete but
                # we can consider this a success.
                self._logger.warning(
                    "not deleting nonexistent deploy/{} from ns/{}".format(
                        app_name_to_delete, namespace
                    )
                )
            else:
                raise
        else:
            self._logger.info(
                "deleted deploy/{} from ns/{}".format(app_name_to_delete, namespace)
            )

    def create_app(self, namespace, name, labels, app):
        """Create App.

        :param str namespace:
        :param str name:
        :param Dict labels:
        :param cloudshell.cp.kubernetes.models.deployment_requests.
            AppDeploymentRequest app:
        :rtype: AppsV1beta1Deployment
        """
        app_selector = {TagsService.get_default_selector(name): name}
        labels.update(app_selector)
        annotations = {}

        meta = V1ObjectMeta(name=name, labels=labels)

        template_meta = V1ObjectMeta(labels=labels, annotations=annotations)

        container = self._prepare_app_container(
            name=app.name,
            image=app.image,
            start_command=app.start_command,
            environment_variables=app.environment_variables,
            compute_spec=app.compute_spec,
            internal_ports=app.internal_ports,
            external_ports=app.external_ports,
        )

        pod_spec = V1PodSpec(containers=[container])
        app_template = V1PodTemplateSpec(metadata=template_meta, spec=pod_spec)
        app_spec = V1DeploymentSpec(
            replicas=app.replicas,
            template=app_template,
            selector={"matchLabels": app_selector},
        )
        deployment = V1Deployment(metadata=meta, spec=app_spec)

        self._logger.info("Creating namespaced deployment for app {}".format(name))
        self._logger.debug("Creating namespaced deployment with the following specs:")
        self._logger.debug(deployment.to_str())

        return self._clients.apps_api.create_namespaced_deployment(
            namespace=namespace, body=deployment, pretty="true"
        )

    @staticmethod
    def _prepare_app_container(
        name,
        image,
        start_command,
        environment_variables,
        compute_spec,
        internal_ports,
        external_ports,
    ):
        """Prepare app.

        :param str start_command:
        :param Dict[str, str] environment_variables:
        :param ApplicationImage image:
        :param AppComputeSpecKubernetes compute_spec:
        :param str name:
        :param List[int] internal_ports:
        :param List[int] external_ports:
        :rtype: V1Container
        """
        container_ports = []
        for port in internal_ports:
            container_ports.append(
                V1ContainerPort(
                    name="{}{}".format(TagsService.INTERNAL_PORT_PREFIX, port),
                    container_port=port,
                )
            )

        for port in external_ports:
            container_ports.append(
                V1ContainerPort(
                    name="{}{}".format(TagsService.EXTERNAL_PORT_PREFIX, port),
                    container_port=port,
                )
            )

        env_list = (
            [
                V1EnvVar(name=key, value=value)
                for key, value in environment_variables.items()
            ]
            if environment_variables
            else []
        )

        command = None
        args = None
        if start_command:
            command = ["/bin/bash", "-c", "--"]
            args = [
                start_command
            ]  # ["while true; do sleep 30; done;"]  # run a task that will never finish

        if image.tag == "latest" or image.tag == "":
            full_image_name = image.name
        else:
            full_image_name = "{name}:{tag}".format(name=image.name, tag=image.tag)

        if compute_spec:
            resources = KubernetesDeploymentService._prepare_resource_request(
                compute_spec
            )

            return V1Container(
                name=name,
                image=full_image_name,
                resources=resources,
                command=command,
                args=args,
                ports=container_ports,
                env=env_list,
            )
        else:
            return V1Container(
                name=name,
                image=full_image_name,
                command=command,
                args=args,
                ports=container_ports,
                env=env_list,
            )

    @staticmethod
    def _prepare_resource_request(compute_spec):
        resources = {}

        if compute_spec.requests.cpu or compute_spec.requests.ram:
            resources["requests"] = {}
        if compute_spec.requests.cpu:
            resources["requests"]["cpu"] = compute_spec.requests.cpu
        if compute_spec.requests.ram:
            resources["requests"]["memory"] = compute_spec.requests.ram

        if compute_spec.limits.cpu or compute_spec.limits.ram:
            resources["limits"] = {}
        if compute_spec.limits.cpu:
            resources["limits"]["cpu"] = compute_spec.limits.cpu
        if compute_spec.limits.ram:
            resources["limits"]["memory"] = compute_spec.limits.ram

        return resources if resources else None

    def wait_until_all_replicas_ready(
        self, namespace, app_name, deployed_app_name, delay=10, timeout=120
    ):
        """Wait until ready.

        :param str namespace:
        :param str app_name:
        :param str deployed_app_name:
        :param int delay:
        :param int timeout:
        :return:
        """
        start_time = time.time()
        while True:
            deployment = self.get_deployment_by_name(namespace, app_name)

            if not deployment:
                raise ValueError("Something went wrong. Deployment {} not found.")

            # check if all replicas are ready
            if deployment.spec.replicas == deployment.status.ready_replicas:
                # all replicas are ready - success
                return

            if time.time() - start_time >= timeout:
                try:
                    query_selector = self._prepare_deployment_default_label_selector(
                        app_name
                    )
                    pods = self._clients.core_api.list_namespaced_pod(
                        namespace=namespace, label_selector=query_selector
                    ).items
                    self._logger.error("Deployment dump:")
                    self._logger.error(str(deployment))
                    self._logger.error("Pods dump:")
                    self._logger.error(str(pods))
                except Exception:
                    self._logger.exception(
                        "Failed to get more data about pods and "
                        "deployment for deployed app {}".format(deployed_app_name)
                    )

                raise TimeoutError(
                    "Timeout waiting for {} replicas to be ready for deployed app {}. "
                    "Please look at the logs for more information".format(
                        deployment.status.replicas, deployed_app_name
                    )
                )

            time.sleep(delay)

    def wait_until_exists(self, namespace, app_name, delay=10, timeout=600):
        """Wait until exist.

        Waits until the deployment called 'app_name' exists in
        Kubernetes regardless of state.

        :param int delay: the time in seconds between each pull
        :param int timeout: timeout in seconds until time out exception will raised
        :param str namespace:
        :param str app_name:
        """
        query_selector = self._prepare_deployment_default_label_selector(app_name)

        start_time = time.time()

        while True:
            result = self._clients.apps_api.list_namespaced_deployment(
                namespace=namespace, label_selector=query_selector
            ).items
            if not result:
                return
            if time.time() - start_time >= timeout:
                raise TimeoutError(
                    "Timeout: Waiting for deployment {} to be deleted".format(app_name)
                )
            time.sleep(delay)

    def _prepare_deployment_default_label_selector(self, app_name):
        query_selector = "{app_selector}=={app_name}".format(
            app_selector=TagsService.get_default_selector(app_name), app_name=app_name
        )
        return query_selector

    def update_deployment(self, namespace, app_name, updated_deployment):
        """Update deployment.

        :param str namespace:
        :param str app_name:
        :param AppsV1beta1Deployment updated_deployment:
        :return:
        """
        api_response = self._clients.apps_api.patch_namespaced_deployment(
            name=app_name, namespace=namespace, body=updated_deployment
        )
        self._logger.debug(
            "Deployment {} in ns/{} updated. Status='{}'".format(
                app_name, namespace, str(api_response.status)
            )
        )

    def get_deployment_by_name(self, namespace, app_name):
        """Get by name.

        :param str namespace:
        :param str app_name:
        :rtype: AppsV1beta1Deployment
        """
        query_selector = self._prepare_deployment_default_label_selector(app_name)
        items = self._clients.apps_api.list_namespaced_deployment(
            namespace=namespace, label_selector=query_selector
        ).items
        if not items:
            return None
        if len(items) > 1:
            raise ValueError(
                "More than a one deployment found with the same app name {}".format(
                    app_name
                )
            )
        return items[0]
