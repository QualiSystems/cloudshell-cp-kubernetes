from cloudshell.cp.core.flows import AbstractPrepareSandboxInfraFlow
from cloudshell.cp.kubernetes.services.tags import TagsService


class PrepareSandboxInfraFlow(AbstractPrepareSandboxInfraFlow):
    def __init__(self, logger, resource_config, service_provider):
        """
        :param logging.Logger logger:
        :param cloudshell.cp.kubernetes.resource_config.KubernetesResourceConfig resource_config:
        :param cloudshell.cp.kubernetes.services.service_provider.ServiceProvider service_provider:
        """
        super().__init__(logger)
        self._resource_config = resource_config
        self._service_provider = service_provider

    def prepare_subnets(self, request_actions):
        self._validate_single_subnet_mode(request_actions)
        return {}

    def create_ssh_keys(self, request_actions):
        # todo - alexaz - create the ssh key and returto cloudshell
        # access_keys_action = single(request_actions, lambda x: isinstance(x, CreateKeys))
        # access_keys_action_results = CreateKeysActionResult(access_keys_action.actionId)
        pass

    def prepare_cloud_infra(self, request_actions):
        # deploy_app = request_actions.deploy_app  # type: KubernetesDeployApp

        # generate namespace name for sandbox
        requested_namespace_name = self._service_provider.namespace_service.get_namespace_name_for_sandbox(
            self._resource_config.sandbox_id)
        self._logger.debug("Creating namespace '{}'".format(requested_namespace_name))

        # todo - alexaz - add more labels like 'createdby', 'owner', etc and add annotations
        labels = {TagsService.SANDBOX_ID: self._resource_config.sandbox_id}

        # check if namesapce already exists
        namespace_obj = self._service_provider.namespace_service.get_single_by_id(self._resource_config.sandbox_id)
        if not namespace_obj:
            # create namespace for sandbox
            created_namespace = self._service_provider.namespace_service.create(requested_namespace_name, labels, None)
            self._logger.info("Created namespace '{}'".format(created_namespace.metadata.name))
        else:
            self._logger.info("Namespace '{}' already exists".format(requested_namespace_name))

        # return PrepareCloudInfraResult(actionId=request_actions.prepare_cloud_infra.actionId)

    def _validate_single_subnet_mode(self, actions):
        if len(actions.prepare_subnets) > 1:
            raise ValueError("Multiple subnets are not supported by the Kubernetes Shell")
