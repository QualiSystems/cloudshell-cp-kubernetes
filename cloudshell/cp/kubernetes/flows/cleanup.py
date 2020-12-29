from cloudshell.cp.core.flows import AbstractCleanupSandboxInfraFlow


class CleanupSandboxInfraFlow(AbstractCleanupSandboxInfraFlow):
    def __init__(self, logger, resource_config, service_provider):
        """
        :param logging.Logger logger:
        :param cloudshell.cp.kubernetes.resource_config.KubernetesResourceConfig resource_config:
        :param cloudshell.cp.kubernetes.services.service_provider.ServiceProvider service_provider:
        """
        super().__init__(logger)
        self._logger = logger
        self._resource_config = resource_config
        self._service_provider = service_provider

    def cleanup_sandbox_infra(self, request_actions):
        self._service_provider.namespace_service.terminate(self._resource_config.sandbox_id)
