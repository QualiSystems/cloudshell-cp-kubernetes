from functools import lru_cache

from cloudshell.cp.kubernetes.services.deployment import KubernetesDeploymentService
from cloudshell.cp.kubernetes.services.namespace import KubernetesNamespaceService
from cloudshell.cp.kubernetes.services.networking import KubernetesNetworkingService


class ServiceProvider(object):
    def __init__(self, api_clients, logger):
        self.api_clients = api_clients
        self.logger = logger

    @property
    @lru_cache()
    def networking_service(self):
        return KubernetesNetworkingService(self.logger, self.api_clients)

    @property
    @lru_cache()
    def deployment_service(self):
        return KubernetesDeploymentService(self.logger, self.api_clients)

    @property
    @lru_cache()
    def namespace_service(self):
        return KubernetesNamespaceService(self.logger, self.api_clients)
