import socket
import time

from dns.resolver import Resolver, NXDOMAIN
from kubernetes.client import V1ObjectMeta, V1Service, V1ServiceSpec, V1ServicePort, V1ServiceList, \
    V1DeleteOptions
from kubernetes.client.rest import ApiException

from cloudshell.cp.kubernetes.services.tags import TagsService
from cloudshell.cp.kubernetes.services.vm_details import VmDetailsProvider


class KubernetesNetworkingService(object):
    def __init__(self, logger, clients, cancellation_manager):
        """

        :param logging.Logger logger:
        :param cloudshell.cp.kubernetes.models.clients.KubernetesClients clients:
        :param cloudshell.cp.core.cancellation_manager.CancellationContextManager cancellation_manager:
        """
        self._logger = logger
        self._clients = clients
        self._cancellation_manager = cancellation_manager

    def create_internal_external_set(self, namespace, name, labels, internal_ports, external_ports,
                                     external_service_type):
        """
        :param str external_service_type:
        :param str namespace:
        :param str name:
        :param dict labels:
        :param List[int] internal_ports:
        :param List[int] external_ports:
        :rtype: List[V1Service]
        """

        # add app label selector so we can find the services of an app using a single query
        service_labels = dict(labels)
        service_labels.update({TagsService.SERVICE_APP_NAME: name})

        services = list()
        if internal_ports:
            internal_service_labels = dict(service_labels)
            internal_service_labels.update({TagsService.INTERNAL_SERVICE: 'true'})
            service = self._create(namespace=namespace,
                                   name=name,
                                   app_name=name,
                                   labels=internal_service_labels,
                                   ports=internal_ports,
                                   spec_type='ClusterIP')
            services.append(service)
            self._logger.info('Created internal service for app {}'.format(name))

        if external_ports:
            external_service_labels = dict(service_labels)
            external_service_labels.update({TagsService.EXTERNAL_SERVICE: 'true'})
            service_name = self._format_external_service_name(name)
            service = self._create(namespace=namespace,
                                   name=service_name,
                                   app_name=name,
                                   labels=external_service_labels,
                                   ports=external_ports,
                                   spec_type=external_service_type)
            services.append(service)
            self._logger.info('Created external service for app {}'.format(name))

        return services

    def _format_external_service_name(self, name):
        return "{}-{}".format(name, TagsService.EXTERNAL_SERVICE_POSTFIX)

    def delete_internal_external_set(self, service_name_to_delete, namespace):
        """
        :param str namespace:
        :param str service_name_to_delete:
        """
        # delete internal service if exists
        self.delete_service(service_name_to_delete, namespace)

        # delete external service if exists
        external_service_name_to_delete = self._format_external_service_name(service_name_to_delete)
        self.delete_service(external_service_name_to_delete, namespace)

    def _create(self,
                namespace,
                name,
                app_name,
                labels,
                ports,
                spec_type):
        """
        :param str namespace:
        :param str name:
        :param str app_name:
        :param dict labels:
        :param List[int] ports:
        :param str spec_type:
        :rtype: V1Service
        """

        core_v1_api = self._clients.core_api
        annotations = {}  # todo add annotations to services

        meta = V1ObjectMeta(name=name, labels=labels, annotations=annotations)
        service_ports = list()

        for port in ports:
            service_ports.append(V1ServicePort(name="port" + str(port), port=port, target_port=port, protocol="TCP"))

        selector_tag = {TagsService.get_default_selector(app_name): app_name}

        if spec_type == "LoadBalancer":
            allowed_ips = None  # todo - alexaz - add option to restrict source ips
            specs = V1ServiceSpec(ports=service_ports,
                                  selector=selector_tag,
                                  type=spec_type,
                                  load_balancer_source_ranges=allowed_ips)
        else:
            specs = V1ServiceSpec(ports=service_ports,
                                  selector=selector_tag,
                                  type=spec_type)

        service = V1Service(metadata=meta, spec=specs)
        return core_v1_api.create_namespaced_service(namespace=namespace,
                                                     body=service,
                                                     pretty='true')

    def _get_service_app_name_selector(self, app_name):
        query_selector = "{selector}=={app_name}".format(
            selector=TagsService.SERVICE_APP_NAME,
            app_name=app_name)
        return query_selector

    def get_all(self):
        return self._clients.core_api.list_service_for_all_namespaces(label_selector=TagsService.SANDBOX_ID)

    def get_services_by_app_name(self, namespace, app_name):
        """
        :param str namespace:
        :param str app_name:
        :rtype: List[V1Service]
        """
        selector_tag = self._get_service_app_name_selector(app_name)
        return self._clients.core_api.list_namespaced_service(namespace=namespace,
                                                              label_selector=selector_tag).items

    def get_ext_services_by_app_name(self, namespace, app_name):
        """
        :param str namespace:
        :param str app_name:
        :rtype: List[V1Service]
        """
        selector_tag = self._get_service_app_name_selector(app_name)
        selector_tag = "{},{}=={}".format(selector_tag, TagsService.EXTERNAL_SERVICE, 'true')
        return self._clients.core_api.list_namespaced_service(namespace=namespace,
                                                              label_selector=selector_tag).items

    def get_app_ext_address(self, app_name, namespace, max_retries=1, timeout=1):
        attempt = 0
        address = ""
        while attempt < max_retries:
            ext_service = self.get_ext_services_by_app_name(namespace, app_name)
            if ext_service:
                address = VmDetailsProvider.get_external_ip(ext_service[0])
                if address:
                    return address if self.is_ipaddr(address) else self.resolve_hostname(
                        address, max_retries - attempt, timeout)
            attempt += 1
            attempt < max_retries and time.sleep(timeout)
        return address

    @staticmethod
    def is_ipaddr(address):
        try:
            socket.inet_aton(address)
            return True
        except socket.error:
            return False

    @staticmethod
    def resolve_hostname(hostname, max_retries=1, timeout=1):
        attempt = 0
        address = hostname
        resolver = Resolver()
        resolver.nameservers = ['8.8.8.8']
        while attempt < max_retries:
            try:
                address = socket.gethostbyname(hostname)
                break
            except:
                try:
                    address = resolver.resolve(hostname)[0]
                    break
                except NXDOMAIN:
                    # wait
                    attempt += 1
                    attempt < max_retries and time.sleep(timeout)
        return address

    def get_int_services_by_app_name(self, namespace, app_name):
        """
        :param str namespace:
        :param str app_name:
        :rtype: List[V1Service]
        """
        selector_tag = self._get_service_app_name_selector(app_name)
        selector_tag = "{},{}=={}".format(selector_tag, TagsService.INTERNAL_SERVICE, 'true')
        return self._clients.core_api.list_namespaced_service(namespace=namespace,
                                                              label_selector=selector_tag).items

    def get_app_int_address(self, app_name, namespace):
        int_service = self.get_int_services_by_app_name(namespace, app_name)
        address = app_name
        if int_service:
            address = VmDetailsProvider.get_internal_ip(int_service[0])
        return address

    def filter_by_label(self, filter_query):
        """
        :param str filter_query:
        :rtype: V1ServiceList
        """
        return self._clients.core_api.list_service_for_all_namespaces(label_selector=filter_query)

    def delete_service(self, service_name_to_delete, namespace):
        """
        :param str namespace:
        :param str service_name_to_delete:
        :return:
        """
        try:
            delete_options = V1DeleteOptions(propagation_policy='Foreground',
                                             grace_period_seconds=0)
            self._clients.core_api.delete_namespaced_service(name=service_name_to_delete,
                                                             namespace=namespace,
                                                             body=delete_options)
        except ApiException as e:
            if e.status == 404:
                # Service does not exist, nothing to delete but
                # we can consider this a success.
                self._logger.warning(
                    'not deleting nonexistent service/{} from ns/{}'.format(service_name_to_delete, namespace))
            else:
                raise
        else:
            self._logger.info('deleted service/{} from ns/{}'.format(service_name_to_delete, namespace))
