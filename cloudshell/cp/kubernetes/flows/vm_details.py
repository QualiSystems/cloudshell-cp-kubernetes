from cloudshell.cp.core.flows import AbstractVMDetailsFlow


class VmDetialsFlow(AbstractVMDetailsFlow):
    def __init__(self, logger, resource_config, service_provider, vm_details_provider, cancellation_manager):
        """
        :param logging.Logger logger:
        :param cloudshell.cp.kubernetes.resource_config.KubernetesResourceConfig resource_config:
        :param cloudshell.cp.kubernetes.services.service_provider.ServiceProvider service_provider:
        :param cloudshell.cp.kubernetes.services.vm_details.VmDetailsProvider vm_details_provider:
        :param cloudshell.cp.core.cancellation_manager.CancellationContextManager cancellation_manager:
        """
        super().__init__(logger)
        self._resource_config = resource_config
        self._service_provider = service_provider
        self._vm_details_provider = vm_details_provider
        self._cancelation_manager = cancellation_manager

    def _get_vm_details(self, deployed_app):
        """
        :param cloudshell.cp.kubernetes.models.deployed_app.KubernetesDeployedApp deployed_app:
        """
        self._logger.info('Creating vm details for {} vms'.format(len(deployed_app.name)))

        services = self._service_provider.networking_service.get_services_by_app_name(namespace=deployed_app.namespace,
                                                                                      app_name=deployed_app.name)

        deployment = self._service_provider.deployment_service.get_deployment_by_name(namespace=deployed_app.namespace,
                                                                                      app_name=deployed_app.name)

        return self._vm_details_provider.create_vm_details(services=services,
                                                           deployment=deployment,
                                                           deployed_app=deployed_app,
                                                           deploy_app_name=deployed_app.name)
