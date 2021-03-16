from cloudshell.cp.core.flows import AbstractVMDetailsFlow


class VmDetialsFlow(AbstractVMDetailsFlow):
    def __init__(self, logger, resource_config, service_provider, vm_details_provider):
        """
        :param logging.Logger logger:
        :param cloudshell.cp.kubernetes.resource_config.KubernetesResourceConfig resource_config:
        :param cloudshell.cp.kubernetes.services.service_provider.ServiceProvider service_provider:
        :param cloudshell.cp.kubernetes.services.vm_details.VmDetailsProvider vm_details_provider:
        """
        super().__init__(logger)
        self._resource_config = resource_config
        self._service_provider = service_provider
        self._vm_details_provider = vm_details_provider

    def _get_vm_details(self, deployed_app):
        """
        :param cloudshell.cp.kubernetes.models.deployed_app.KubernetesDeployedApp deployed_app:
        """
        self._logger.info('Creating vm details for {} vms'.format(len(deployed_app.name)))

        services = self._service_provider.networking_service.get_services_by_app_name(
            namespace=deployed_app.namespace,
            app_name=deployed_app.kubernetes_name)

        deployment = self._service_provider.deployment_service.get_deployment_by_name(
            namespace=deployed_app.namespace,
            app_name=deployed_app.kubernetes_name)

        vm_details = self._vm_details_provider.create_vm_details(services=services,
                                                                 deployment=deployment,
                                                                 deployed_app=deployed_app,
                                                                 deploy_app_name=deployed_app.name)

        self._validate_external_ip(vm_details.vmInstanceData, deployed_app)

        return vm_details

    def _validate_external_ip(self, vm_inst_data, deployed_app):
        ext_ip = next(filter(lambda x: x.key == "External IP", vm_inst_data), None)
        if ext_ip and not ext_ip.value or not self._service_provider.networking_service.is_ipaddr(ext_ip.value):
            if deployed_app.wait_for_ip.lower() == "true":
                ext_ip.value = self._service_provider.networking_service.get_app_ext_address(
                    deployed_app.kubernetes_name,
                    deployed_app.namespace,
                    max_retries=6, timeout=5)
            self._logger.debug("Ext IP: {}".format(ext_ip.value))
