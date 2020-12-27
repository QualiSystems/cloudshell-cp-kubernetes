from cloudshell.cp.core.request_actions.models import CleanupNetworkResult


class CleanupSandboxInfraFlow(object):
    def __init__(self, logger, resource_config, service_provider):
        """
        :param logging.Logger logger:
        :param cloudshell.cp.kubernetes.resource_config.KubernetesResourceConfig resource_config:
        :param cloudshell.cp.kubernetes.services.service_provider.ServiceProvider service_provider:
        """
        self._logger = logger
        self._resource_config = resource_config
        self._service_provider = service_provider

    def cleanup(self, sandbox_id, cleanup_action):
        """
        :param str sandbox_id:
        :param CleanupNetwork cleanup_action:
        :return:
        """
        self._service_provider.namespace_service.terminate(sandbox_id)
        return CleanupNetworkResult(cleanup_action.actionId)
