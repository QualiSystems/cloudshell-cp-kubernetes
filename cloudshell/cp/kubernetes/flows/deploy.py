import socket
import time
import traceback

from dns.resolver import Resolver, NXDOMAIN

from cloudshell.cp.core.flows import AbstractDeployFlow
from cloudshell.cp.core.request_actions.models import DeployAppResult, Attribute

from cloudshell.cp.kubernetes.common.additional_data_keys import DeployedAppAdditionalDataKeys
from cloudshell.cp.kubernetes.common.utils import convert_app_name_to_valid_kubernetes_name, convert_to_int_list, \
    generate_short_unique_string
from cloudshell.cp.kubernetes.models.deploy_app import KubernetesDeployApp
from cloudshell.cp.kubernetes.models.deployment_requests import ApplicationImage, AppDeploymentRequest, \
    AppComputeSpecKubernetes, AppComputeSpecKubernetesResources
from cloudshell.cp.kubernetes.services.tags import TagsService


class DeployFlow(AbstractDeployFlow):
    def __init__(self, logger, resource_config, service_provider, vm_details_provider):
        """
        :param logging.Logger logger:
        :param cloudshell.cp.kubernetes.resource_config.KubernetesResourceConfig resource_config:
        :param cloudshell.cp.kubernetes.services.service_provider.ServiceProvider service_provider:
        :param cloudshell.cp.kubernetes.services.vm_details.VmDetailsProvider vm_details_provider:
        """
        super().__init__(logger)
        self._resource_config = resource_config
        self._service_provider = service_provider
        self._vm_details_provider = vm_details_provider

    def _deploy(self, request_actions):
        """
        :param cloudshell.cp.core.request_actions.DeployVMRequestActions request_actions:
        """
        deploy_app = request_actions.deploy_app
        if not isinstance(deploy_app, KubernetesDeployApp):
            raise Exception("Deployment Path is not registered")
        sandbox_tag = {TagsService.SANDBOX_ID: self._resource_config.sandbox_id}

        # deployment_model = create_deployment_model_from_action(deploy_action)
        kubernetes_app_name = convert_app_name_to_valid_kubernetes_name(deploy_app.app_name)
        cloudshell_name = self._generate_cloudshell_deployed_app_name(kubernetes_app_name)

        namespace_obj = self._service_provider.namespace_service.get_single_by_id(self._resource_config.sandbox_id)
        self._validate_namespace(namespace_obj, self._resource_config.sandbox_id)
        namespace = namespace_obj.metadata.name

        # todo create annotations

        internal_ports = convert_to_int_list(deploy_app.internal_ports)
        external_ports = convert_to_int_list(deploy_app.external_ports)

        try:
            created_services = self._service_provider.networking_service.create_internal_external_set(
                namespace=namespace,
                name=kubernetes_app_name,
                labels=dict(sandbox_tag),
                internal_ports=internal_ports,
                external_ports=external_ports,
                external_service_type=self._resource_config.external_service_type)

            deployment_labels = dict(sandbox_tag)
            for created_service in created_services:
                deployment_labels.update(created_service.spec.selector)

            image = ApplicationImage(deploy_app.docker_image_name,
                                     deploy_app.docker_image_tag)

            compute_spec = self._get_compute_spec(deploy_app)
            replicas = self._get_and_validate_replicas_number(deploy_app)
            environment_variables = self._get_environment_variables_dict(deploy_app.environment_variables)

            deployment_request = AppDeploymentRequest(name=kubernetes_app_name,
                                                      image=image,
                                                      start_command=deploy_app.start_command,
                                                      environment_variables=environment_variables,
                                                      compute_spec=compute_spec,
                                                      internal_ports=internal_ports,
                                                      external_ports=external_ports,
                                                      replicas=replicas)

            created_deplomyent = self._service_provider.deployment_service.create_app(
                namespace=namespace,
                name=kubernetes_app_name,
                labels=deployment_labels,
                app=deployment_request)

            vm_details = self._vm_details_provider.create_vm_details(created_services, created_deplomyent)

            additional_data = self._create_additional_data(namespace, replicas, deploy_app.wait_for_replicas)

            # prepare result
            return DeployAppResult(deploy_app.actionId,
                                   vmUuid=kubernetes_app_name,
                                   vmName=cloudshell_name,
                                   vmDetailsData=vm_details,
                                   deployedAppAdditionalData=additional_data,
                                   deployedAppAttributes=[
                                       Attribute("Public IP",
                                                 self._service_provider.networking_service.get_app_ext_address(
                                                     kubernetes_app_name, namespace))],
                                   deployedAppAddress=self._service_provider.networking_service.get_app_int_address(
                                       kubernetes_app_name,
                                       namespace))  # todo - what address to use here?
        except:
            self._do_rollback_safely(namespace=namespace,
                                     cs_app_name=deploy_app.actionParams.appName,
                                     kubernetes_app_name=kubernetes_app_name)
            # raise the original exception to log it properly
            raise

    def _generate_cloudshell_deployed_app_name(self, kubernetes_app_name):
        return "{}-{}".format(kubernetes_app_name, generate_short_unique_string())

    def _get_compute_spec(self, deployment_model):
        compute_spec = None
        if deployment_model.cpu_limit or deployment_model.ram_limit or deployment_model.cpu_request or deployment_model.ram_request:
            compute_spec = AppComputeSpecKubernetes(
                requests=AppComputeSpecKubernetesResources(cpu=deployment_model.cpu_request,
                                                           ram=deployment_model.ram_request),
                limits=AppComputeSpecKubernetesResources(cpu=deployment_model.cpu_limit,
                                                         ram=deployment_model.ram_limit))

        # todo - add validation: limit without request will not work. need to raise exc

        return compute_spec

    def _validate_namespace(self, namespace_obj, sandbox_id):
        if not namespace_obj:
            raise ValueError("Namespace for sandbox '{}' not found".format(sandbox_id))

    def _get_and_validate_replicas_number(self, deployment_model):
        """
        :param data_model.KubernetesService deployment_model:
        :rtype: int
        """
        replicas = int(deployment_model.replicas)
        if replicas < 1:
            raise ValueError("The number of replicas for the application must be 1 or greater")
        return replicas

    def _create_additional_data(self, namespace, replicas, wait_for_replicas_to_be_ready):
        """
        :param str namespace:
        :param int replicas:
        :param int wait_for_replicas_to_be_ready:
        :rtype: Dict
        """
        return {
            DeployedAppAdditionalDataKeys.NAMESPACE: namespace,
            DeployedAppAdditionalDataKeys.REPLICAS: replicas,
            DeployedAppAdditionalDataKeys.WAIT_FOR_REPLICAS_TO_BE_READY: wait_for_replicas_to_be_ready
        }

    def _get_environment_variables_dict(self, environment_variables):
        """
        :param str environment_variables:
        :rtype: Dict[str, str]
        """
        if not environment_variables or not environment_variables.strip():
            return None

        env_list = environment_variables.strip().split(',')

        env_dict = {}

        for env_str in env_list:
            try:
                key, value = env_str.split('=', 2)
                env_dict.update({key.strip(): value.strip()})
            except ValueError:
                self._logger.exception(
                    "Cannot unpack env var '{}' to key value pair. Missing '=' sign?".format(env_str))
                raise ValueError("Cannot parse environment variable '{}'. Expected format: key=value".format(env_str))

        return env_dict

    def _do_rollback_safely(self, namespace, cs_app_name, kubernetes_app_name):
        """
        :param str cs_app_name: object
        :param str namespace:
        :param str kubernetes_app_name:
        :return:
        """
        self._logger.info('Doing rollback for app {} in ns/{}'.format(cs_app_name, namespace))

        try:
            self._service_provider.networking_service.delete_internal_external_set(kubernetes_app_name, namespace)
            self._service_provider.deployment_service.delete_app(app_name_to_delete=kubernetes_app_name,
                                                                 namespace=namespace)
        except:
            self._logger.error('Failed to do rollback for app {} in ns/{}. Error:'
                               .format(cs_app_name, namespace, traceback.format_exc()))
