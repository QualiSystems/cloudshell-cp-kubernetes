class KubernetesClients(object):

    def __init__(self, api_client, core_api, apps_api):
        """
        :param kubernetes.client.AppsV1Api apps_api:
        :param kubernetes.client.ApiClient api_client:
        :param kubernetes.client.CoreV1Api core_api:
        """
        self._api_client = api_client
        self.apps_api = apps_api
        self.core_api = core_api
