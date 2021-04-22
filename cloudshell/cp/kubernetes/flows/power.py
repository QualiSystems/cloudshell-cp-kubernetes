class PowerFlow(object):
    def __init__(self, logger, resource_config, service_provider):
        """Init.

        :param logging.Logger logger:
        :param cloudshell.cp.kubernetes.resource_config.
            KubernetesResourceConfig resource_config:
        :param cloudshell.cp.kubernetes.services.service_provider.
            ServiceProvider service_provider:
        """
        self._logger = logger
        self._resource_config = resource_config
        self._service_provider = service_provider

    def power_on(self, deployed_app):
        """Power On.

        :param DeployedAppResource deployed_app:
        :return:
        """
        deployment = self._service_provider.deployment_service.get_deployment_by_name(
            deployed_app.namespace, deployed_app.kubernetes_name
        )

        # set the replicas count to the original number in order to "power on" the app
        deployment.spec.replicas = deployed_app.replicas
        deployment.spec.template.spec.containers[0].ports = []

        self._service_provider.deployment_service.update_deployment(
            namespace=deployed_app.namespace,
            app_name=deployed_app.kubernetes_name,
            updated_deployment=deployment,
        )

        self._logger.info(
            "Replicas number set to {} for app {}".format(
                str(deployed_app.replicas), deployed_app.name
            )
        )

        if deployed_app.wait_for_replicas_to_be_ready > 0:
            self._logger.info(
                "Waiting for all replicas of app {} to be ready. "
                "Timeout set to: {}".format(
                    deployed_app.name, str(deployed_app.wait_for_replicas_to_be_ready)
                )
            )
            self._service_provider.deployment_service.wait_until_all_replicas_ready(
                namespace=deployed_app.namespace,
                app_name=deployed_app.kubernetes_name,
                deployed_app_name=deployed_app.name,
                timeout=deployed_app.wait_for_replicas_to_be_ready,
            )

        self._logger.info("App {} powered on.".format(deployed_app.name))

    def power_off(self, deployed_app):
        """Power Off.

        :param DeployedAppResource deployed_app:
        :return:
        """
        deployment = self._service_provider.deployment_service.get_deployment_by_name(
            deployed_app.namespace, deployed_app.kubernetes_name
        )

        # set the replicas count to 0 in order to "power off" the app
        deployment.spec.replicas = 0
        deployment.spec.template.spec.containers[0].ports = []

        self._service_provider.deployment_service.update_deployment(
            namespace=deployed_app.namespace,
            app_name=deployed_app.kubernetes_name,
            updated_deployment=deployment,
        )

        self._logger.info(
            "App {}({}) powered off. Replicas count set to 0".format(
                deployed_app.name, deployed_app.kubernetes_name
            )
        )
