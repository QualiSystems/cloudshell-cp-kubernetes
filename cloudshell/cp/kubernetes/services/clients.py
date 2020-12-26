import base64
import os
import re
import boto3
from botocore.signers import RequestSigner
from kubernetes.client import ApiClient, Configuration
from kubernetes.client.api import AppsV1Api, CoreV1Api
from kubernetes.config import new_client_from_config, ConfigException
from kubernetes.config.kube_config import KubeConfigLoader, KubeConfigMerger

from cloudshell.cp.kubernetes.models.clients import KubernetesClients


class ApiClientsProvider(object):

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

        eks_loader = EKSKubeConfigLoader(config_path, aws_access_key_id, aws_secret_access_key)
        eks_loader.load_and_set(client_config)
        return ApiClient(configuration=client_config)


class EKSKubeConfigLoader(KubeConfigLoader):
    STS_TOKEN_EXPIRES_IN = 60

    def __init__(self, config_path=None, aws_access_key_id=None, aws_secret_access_key=None):
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
        session = boto3.session.Session(aws_access_key_id=self._aws_access_key_id,
                                        aws_secret_access_key=self._aws_secret_access_key)

        client = session.client('sts', region_name=region)
        service_id = client.meta.service_model.service_id

        signer = RequestSigner(
            service_id,
            region,
            'sts',
            'v4',
            session.get_credentials(),
            session.events
        )

        params = {
            'method': 'GET',
            'url': 'https://sts.{}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15'.format(region),
            'body': {},
            'headers': {
                'x-k8s-aws-id': cluster_id
            },
            'context': {}
        }

        signed_url = signer.generate_presigned_url(
            params,
            region_name=region,
            expires_in=self.STS_TOKEN_EXPIRES_IN,
            operation_name=''
        )

        base64_url = base64.urlsafe_b64encode(signed_url.encode('utf-8')).decode('utf-8')

        # remove any base64 encoding padding:
        return 'Bearer k8s-aws-v1.' + re.sub(r'=*', '', base64_url)

# super(EKSKubeConfigLoader, self)._load_authentication()
# class ConfigBuilderBase(object):
#     _config_base_template = "apiVersion: v1\n" \
#                             "clusters: \n" \
#                             "- cluster: \n" \
#                             "[[cluster_section]]" \
#                             "  name: {cluster_name}\n" \
#                             "contexts: \n" \
#                             "- context: \n" \
#                             "    cluster: {cluster_name}\n" \
#                             "    user: {username}\n" \
#                             "  name: {cluster_name}-context\n" \
#                             "current-context: {cluster_name}-context\n" \
#                             "kind: Config\n" \
#                             "preferences: {{}}\n" \
#                             "users: \n" \
#                             "- name: {username}\n" \
#                             "  user:\n"
#
#     def build(self, kube_clp):
#         raise NotImplementedError('Base class. Use a derived class instead.')
#
#     def _get_base_template(self, skip_tls_veify=True, certificate_authority=None):
#         cluster_section = self._build_cluster_section(skip_tls_veify, certificate_authority)
#         return self._config_base_template.replace("[[cluster_section]]", cluster_section)
#
#     def _build_cluster_section(self, skip_tls_veify, certificate_authority):
#         cluster_section = ""
#
#         if skip_tls_veify:
#             cluster_section += "    insecure-skip-tls-verify: true\n"
#
#         if certificate_authority:
#             cluster_section += "    certificate-authority: {}\n".format(certificate_authority)
#
#         cluster_section += "    server: {server}\n"
#
#         return cluster_section
#
#
# class BasicAuthConfigBuilder(ConfigBuilderBase):
#     def build(self, kube_clp):
#         """
#         :param data_model.Kubernetes kube_clp:
#         :rtype: str
#         """
#         config_template = super(BasicAuthConfigBuilder, self)._get_base_template()
#         config_template += "    username: {username}\n" \
#                            "    password: {password}\n"
#
#         return config_template.format(cluster_name=kube_clp.cluster_name,
#                                       server=kube_clp.server,
#                                       username=kube_clp.user,
#                                       password=kube_clp.password)
#
#
# class CertificateAuthConfigBuilder(ConfigBuilderBase):
#     def build(self, kube_clp):
#         """
#         :param data_model.Kubernetes kube_clp:
#         :rtype: str
#         """
#         config_template = super(CertificateAuthConfigBuilder, self)._get_base_template()
#         config_template += "    client-certificate-data: {certificate_data}\n" \
#                            "    client-key-data: {key_data}\n"
#
#         certificate_data = self._read_text_file(kube_clp.client_certificate_path)
#         key_data = self._read_text_file(kube_clp.client_key_path)
#
#         return config_template.format(cluster_name=kube_clp.cluster_name,
#                                       server=kube_clp.server,
#                                       certificate_data=certificate_data,
#                                       key_data=key_data,
#                                       username='cloudshell')
#
#     @staticmethod
#     def _read_text_file(file_path):
#         with open(file_path, 'r')as f:
#             return f.read()
#
#     # def _config_builder(self, cluster_name, server, username, password):
#     #     config = "apiVersion: v1\n" \
#     #              "clusters:\n" \
#     #              "- cluster:\n" \
#     #              "    insecure-skip-tls-verify: true\n" \
#     #              "    server: {server}\n" \
#     #              "  name: {cluster_name}\n" \
#     #              "contexts:\n" \
#     #              "- context:\n" \
#     #              "    cluster: {cluster_name}\n" \
#     #              "    user: {username}\n" \
#     #              "  name: {cluster_name}-context\n" \
#     #              "current-context: {cluster_name}-context\n" \
#     #              "kind: Config\n" \
#     #              "preferences: {{}}\n" \
#     #              "users:\n" \
#     #              "- name: {username}\n" \
#     #              "  user:\n" \
#     #              "    password: {password}\n" \
#     #              "    username: {username}\n".format(cluster_name=cluster_name,
#     #                                                  server=server,
#     #                                                  username=username,
#     #                                                  password=password)
#     #     return config
