from cloudshell.cp.core.request_actions.models import DeployApp
from cloudshell.shell.standards.core.resource_config_entities import ResourceAttrRO


class KubernetesDeployApp(DeployApp):
    DEPLOYMENT_PATH = "Kubernetes Cloud Provider 2G.Kubernetes Service"
    docker_image_name = ResourceAttrRO("Image Name", "DEPLOYMENT_PATH")
    docker_image_tag = ResourceAttrRO("Image Tag", "DEPLOYMENT_PATH")
    internal_ports = ResourceAttrRO("Internal Ports", "DEPLOYMENT_PATH")
    external_ports = ResourceAttrRO("External Ports", "DEPLOYMENT_PATH")
    replicas = ResourceAttrRO("Replicas", "DEPLOYMENT_PATH")
    start_command = ResourceAttrRO("Start Command", "DEPLOYMENT_PATH")
    environment_variables = ResourceAttrRO("Environment Variables", "DEPLOYMENT_PATH")
    cpu_request = ResourceAttrRO("CPU Request", "DEPLOYMENT_PATH")
    ram_request = ResourceAttrRO("RAM Request", "DEPLOYMENT_PATH")
    wait_for_replicas = ResourceAttrRO("Wait for Replicas", "DEPLOYMENT_PATH")
    cpu_limit = ResourceAttrRO("CPU Limit", "DEPLOYMENT_PATH")
    ram_limit = ResourceAttrRO("RAM Limit", "DEPLOYMENT_PATH")
    wait_for_ip = ResourceAttrRO("Wait for IP", "DEPLOYMENT_PATH")
