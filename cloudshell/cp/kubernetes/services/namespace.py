from kubernetes.client import V1Namespace, V1ObjectMeta, V1NamespaceList, V1DeleteOptions
from kubernetes.client.rest import ApiException

from cloudshell.cp.kubernetes.services.tags import TagsService


class KubernetesNamespaceService(object):
    TERMINATING_STATUS = "Terminating"

    def __init__(self, logger, clients, cancellation_manager):
        """

        :param logging.Logger logger:
        :param cloudshell.cp.kubernetes.models.self._clientsKubernetesClients clients:
        """
        self._logger = logger
        self._clients = clients
        self.cancellation_manager = cancellation_manager

    def create(self, name, labels, annotations):
        """
        :param str name:
        :param Dict labels:
        :param Dict annotations:
        :rtype: V1Namespace
        """
        # enable_network_policy = {'net.beta.kubernetes.io/network-policy': '{"ingress": {"isolation": "DefaultDeny"}}'}
        # namespace_meta = V1ObjectMeta(name=name, labels=labels, annotations={**enable_network_policy})
        namespace_meta = V1ObjectMeta(name=name, labels=labels, annotations=annotations)
        namespace = V1Namespace(metadata=namespace_meta)

        return self._clients.core_api.create_namespace(body=namespace, pretty='true')

    def get_namespace_name_for_sandbox(self, sandbox_id):
        """
        :param str sandbox_id:
        :rtype: str
        """
        if not sandbox_id:
            return Exception("Sandbox ID not defined.")
        return "cloudshell-{}".format(sandbox_id)
        # return "default"  # todo - alexaz - change this after implementing PrepreSandboxInfra

    def get_all(self):
        """
        :rtype: V1NamespaceList
        """
        filter_query = '{sandbox_id_tag}'.format(sandbox_id_tag=TagsService.SANDBOX_ID)
        # if space_id:
        #     filter_query += ',{tag}={value}'.format(tag=DevboxTags.SPACE_ID, value=space_id)
        # if cloud_account_id:
        #     filter_query += ',{tag}={value}'.format(tag=DevboxTags.CLOUD_ACCOUNT_ID, value=cloud_account_id)

        return self._clients.core_api.list_namespace(label_selector=filter_query)
        # return self._clients.core_api.list_namespace()

    def get_single_by_id(self, sandbox_id):
        """
        :param str sandbox_id:
        :rtype: V1Namespace
        """

        filter_query = '{label}=={value}'.format(label=TagsService.SANDBOX_ID, value=sandbox_id)

        api_result = self.get(filter_query)
        namespaces = list(api_result.items)

        if len(namespaces) > 1:
            raise ValueError("Found multiple namespaces with the same sandbox id '{}'".format(sandbox_id))

        return next(iter(namespaces), None)

    def get(self, filter_query):
        """
        :param str filter_query:
        :rtype: V1NamespaceList
        """
        return self._clients.core_api.list_namespace(label_selector=filter_query)

    def terminate(self, sandbox_id):
        """
        :param str sandbox_id:
        :return:
        """
        # namespaces = self.get_all(clients)
        # tag = TagsService.SANDBOX_ID
        # namespace_to_delete = next(iter([namespace for namespace in namespaces.items
        #                                  if namespace.metadata.labels[tag] == sandbox_id]), None)
        namespace_to_delete = self.get_single_by_id(sandbox_id)
        if namespace_to_delete:
            if self.get_status(namespace_to_delete.metadata.name) == KubernetesNamespaceService.TERMINATING_STATUS:
                return

            body = V1DeleteOptions(grace_period_seconds=5, orphan_dependents=False)
            self._clients.core_api.delete_namespace(name=namespace_to_delete.metadata.name, body=body, pretty='true')

    def get_status(self, namespace_name):
        """
        :param str namespace_name:
        :rtype: str
        """
        try:
            response = self._clients.core_api.read_namespace_status(name=namespace_name)
            return response.status.phase
        except ApiException as exc:
            if exc.reason == 'Not Found' and exc.status == 404:
                return KubernetesNamespaceService.TERMINATING_STATUS
            raise

    # def update_annotation(self, namespace, key: str, value: str):
    #     namespace_meta = V1ObjectMeta(annotations={key: value})
    #     patched_namespace = V1Namespace(metadata=namespace_meta)
    #     Utils.run_and_log_time(func=lambda: self.core_v1_api.patch_namespace(name=namespace.metadata.name,
    #                                                                          body=patched_namespace),
    #                            logger=self._logger)
