from cloudshell.cp.core.request_actions.models import DeployedApp
from cloudshell.cp.kubernetes.common.additional_data_keys import DeployedAppAdditionalDataKeys


class KubernetesDeployedApp(DeployedApp):
    DEPLOYMENT_PATH = "Kubernetes Cloud Provider Shell 2G.Kubernetes Service"

    @property
    def kubernetes_name(self):
        return self.vmdetails.uid

    @property
    def cloudshell_resource_name(self):
        return self.name

    def _get_vm_details_value(self, name):
        return (list(filter(lambda x: x.get("name") == name,
                            self.vmdetails.vm_custom_params)) + [{}])[0].get("value")

    @property
    def namespace(self):
        """
        :rtype: str
        """
        namespace = self._get_vm_details_value(DeployedAppAdditionalDataKeys.NAMESPACE)
        if not namespace:
            raise ValueError("Something went wrong. Couldn't get namespace from custom params for deployed app '{}'"
                             .format(self.name))
        return namespace

    @property
    def replicas(self):
        """
        :rtype: int
        """
        replicas_str = self._get_vm_details_value(DeployedAppAdditionalDataKeys.REPLICAS)
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
        wait_for_replicas = self._get_vm_details_value(
            DeployedAppAdditionalDataKeys.WAIT_FOR_REPLICAS_TO_BE_READY)
        if not wait_for_replicas:
            return 0

        return int(wait_for_replicas)
