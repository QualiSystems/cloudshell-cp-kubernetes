class DeleteInstanceFlow(object):
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

    def delete_instance(self, kubernetes_name, deployed_app_name, namespace):
        """Delete Instance.

        :param srr deployed_app_name:
        :param str namespace:
        :param str kubernetes_name:
        :rtype: None
        """
        self._service_provider.networking_service.delete_internal_external_set(
            service_name_to_delete=kubernetes_name, namespace=namespace
        )

        self._service_provider.deployment_service.delete_app(
            namespace=namespace, app_name_to_delete=kubernetes_name
        )

        # wait untill the entire deployment doesnt exist any more
        # before finishing the operation
        self._service_provider.deployment_service.wait_until_exists(
            namespace=namespace, app_name=kubernetes_name
        )

        self._logger.info(
            "Deleted app {} with UID {} from ns/{}".format(
                deployed_app_name, kubernetes_name, namespace
            )
        )
