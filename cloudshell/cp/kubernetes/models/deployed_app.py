import json

from cloudshell.cp.core.request_actions.models import DeployApp, DeployedApp
from cloudshell.shell.core.driver_context import ResourceContextDetails
from cloudshell.shell.standards.core.resource_config_entities import ResourceAttrRO

from cloudshell.cp.kubernetes.common.additional_data_keys import DeployedAppAdditionalDataKeys
from cloudshell.cp.kubernetes.common.utils import get_custom_params_value


class KubernetesDeployedApp(DeployedApp):
    # def __init__(self, resource_context=None, deployed_app_dict=None):
    #     """
    #     :param ResourceContextDetails resource_context:
    #     """
    #     if resource_context:
    #         # self.app_request_dict = json.loads(resource_context.app_context.app_request_json)
    #         self.deployed_app_dict = json.loads(resource_context.app_context.deployed_app_json)
    #
    #     elif deployed_app_dict:
    #         self.deployed_app_dict = deployed_app_dict
    #
    #     self.vm_details = self.deployed_app_dict['vmdetails']
    #     self.vm_custom_params = self.vm_details['vmCustomParams']

    # cloudshell_resource_name = ResourceAttrRO("name", "DEPLOYMENT_PATH")

    # @property
    # def kubernetes_name(self):
    #     self.
    #     return self.vm_details['uid']

    # kubernetes_name_name = ResourceAttrRO("uid", "DEPLOYMENT_PATH")

    @property
    def namespace(self):
        """
        :rtype: str
        """
        namespace = self.vmdetails.vm_custom_params.get(DeployedAppAdditionalDataKeys.NAMESPACE)
        if not namespace:
            raise ValueError("Something went wrong. Couldn't get namespace from custom params for deployed app '{}'"
                             .format(self.name))
        return namespace

    @property
    def replicas(self):
        """
        :rtype: int
        """
        replicas_str = self.vmdetails.vm_custom_params.get(DeployedAppAdditionalDataKeys.REPLICAS)
        if not replicas_str:
            raise ValueError("Something went wrong. Couldn't get replicas from custom params for deployed app '{}'"
                             .format(self.name))

        try:
            return int(replicas_str)
        except:
            raise ValueError("Something went wrong. Couldn't parse replicas value {replicas} from custom params data "
                             "for deployed app '{deployed_app}' "
                             .format(deployed_app=self.name, replicas=replicas_str))

    @property
    def wait_for_replicas_to_be_ready(self):
        """
        :rtype: int
        """
        wait_for_replicas = self.vmdetails.vm_custom_params.get(
            DeployedAppAdditionalDataKeys.WAIT_FOR_REPLICAS_TO_BE_READY)
        if not wait_for_replicas:
            return 0

        return int(wait_for_replicas)
