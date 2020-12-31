from cloudshell.api.cloudshell_api import CloudShellAPISession

from cloudshell.cp.kubernetes.models.deployed_app import KubernetesDeployedApp


class RefreshIpFlow(object):
    def __init__(self, logger, resource_config, service_provider):
        """
        :param logging.Logger logger:
        :param cloudshell.cp.kubernetes.resource_config.KubernetesResourceConfig resource_config:
        :param cloudshell.cp.kubernetes.services.service_provider.ServiceProvider service_provider:
        """
        super().__init__(logger)
        self._resource_config = resource_config
        self._service_provider = service_provider

    def refresh_ip(self, deployed_app):
        """
        :param cloudshell.cp.kubernetes.models.deployed_app.KubernetesDeployedApp deployed_app:
        :return:
        """
        ext_ip = self._service_provider.networking_service.get_app_ext_address(deployed_app.kubernetes_name,
                                                                               deployed_app.namespace)
        if ext_ip:
            cs_api = self._resource_config.api # type: CloudShellAPISession
            cs_api.SetAttributeValue(deployed_app.name, "Public IP", ext_ip)
