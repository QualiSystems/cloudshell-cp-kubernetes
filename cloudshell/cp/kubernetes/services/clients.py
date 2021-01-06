import os
import botocore.session
from awscli.customizations.eks.get_token import STSClientFactory, TokenGenerator
from kubernetes.client import ApiClient, Configuration
from kubernetes.client.api import AppsV1Api, CoreV1Api
from kubernetes.config import new_client_from_config, ConfigException
from kubernetes.config.kube_config import KubeConfigLoader, KubeConfigMerger

from cloudshell.cp.kubernetes.models.clients import KubernetesClients


class ApiClientsProvider(object):
    def __init__(self, logger):
        self._logger = logger

    def get_api_clients(self, resource_config):
        """
        :param cloudshell.cp.kubernetes.resource_config.KubernetesResourceConfig resource_config:
        """
        if not os.path.isfile(resource_config.config_file_path):
            raise ValueError(
                "Config File Path is invalid. Cannot open file '{}'.".format(resource_config.config_file_path))

        # todo - alexaz - Need to add support for urls so that we can download a config file from a central location and
        # todo          - also have the config file password protected.
        if resource_config.aws_access_key_id and resource_config.aws_secret_access_key:
            # self._logger.debug("EKS config for, key-ID {}, secret-key {}".format(resource_config.aws_access_key_id,
            #                                                                      resource_config.aws_secret_access_key))
            api_client = self._new_client_from_eks_config(resource_config.config_file_path,
                                                          resource_config.aws_access_key_id,
                                                          resource_config.aws_secret_access_key)
        else:
            api_client = new_client_from_config(config_file=resource_config.config_file_path)
        core_api = CoreV1Api(api_client=api_client)
        apps_api = AppsV1Api(api_client=api_client)

        return KubernetesClients(api_client, core_api, apps_api)

    def _new_client_from_eks_config(self, config_path=None,
                                    aws_access_key_id=None,
                                    aws_secret_access_key=None):
        client_config = type.__call__(Configuration)

        eks_loader = EKSKubeConfigLoader(self._logger, config_path, aws_access_key_id, aws_secret_access_key)
        eks_loader.load_and_set(client_config)
        return ApiClient(configuration=client_config)


class EKSKubeConfigLoader(KubeConfigLoader):
    STS_TOKEN_EXPIRES_IN = 60

    def __init__(self, logger, config_path=None, aws_access_key_id=None, aws_secret_access_key=None):
        self._logger = logger
        kcfg = KubeConfigMerger(config_path)

        if kcfg.config is None:
            raise ConfigException(
                'Invalid kube-config file. '
                'No configuration found.')
        super(EKSKubeConfigLoader, self).__init__(kcfg.config, config_base_path=None)
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key

    def _load_authentication(self):
        exec_args = self._user.value.get("exec", {}).get("args")
        region = exec_args[exec_args.index("--region") + 1]
        cluster_id = exec_args[exec_args.index("--cluster-name") + 1]
        if not region or not cluster_id:
            raise ConfigException("Cannot extract region and cluster-name for user exec.args.")
        self.token = self._get_eks_bearer_token(cluster_id, region)

    def _get_eks_bearer_token(self, cluster_id, region):
        work_session = botocore.session.get_session()
        work_session.set_credentials(self._aws_access_key_id, self._aws_secret_access_key)
        client_factory = STSClientFactory(work_session)
        sts_client = client_factory.get_sts_client(region_name=region)
        token = TokenGenerator(sts_client).get_token(cluster_id)
        token = "Bearer {}".format(token)
        # self._logger.debug("EKS Token: {}".format(token))
        return token
