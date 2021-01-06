class AutolaodFlow(object):

    def __init__(self, api_clients):
        """
        :param cloudshell.cp.kubernetes.models.clients.KubernetesClients api_clients:
        """
        self.api_clients = api_clients

    def validate_config(self, cloud_provider_resource):
        """
        :param cloudshell.cp.kubernetes.resource_config.KubernetesResourceConfig cloud_provider_resource:
        :return:
        """

        # list nodes and make sure we have 1 or more nodes just to check authentication works
        nodes = self.api_clients.core_api.list_node(watch=False)
        if not nodes or len(nodes.items) < 1:
            raise ValueError("Cluster '{}' has zero (0) nodes".format(cloud_provider_resource.name))
