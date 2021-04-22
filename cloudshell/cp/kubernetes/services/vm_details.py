from cloudshell.cp.core.request_actions.models import VmDetailsData, VmDetailsProperty

from cloudshell.cp.kubernetes.common.utils import first_or_default
from cloudshell.cp.kubernetes.services.tags import TagsService


class VmDetailsProvider(object):
    def create_vm_details(
        self, services, deployment, deployed_app=None, deploy_app_name=""
    ):
        """Create VM details.

        :param List[V1Service] services:
        :param kubernetes.client.AppsV1beta1Deployment deployment:
        :param str deploy_app_name:
        :return:
        """
        vm_instance_data = self._get_vm_instance_data(
            services, deployment, deployed_app
        )

        return VmDetailsData(
            vmInstanceData=vm_instance_data, vmNetworkData=[], appName=deploy_app_name
        )

    def _get_vm_instance_data(self, services, deployment, deployed_app):
        """Get VM instance data.

        :param List[V1Service] services:
        :param ubernetes.client.AppsV1beta1Deployment deployment:
        :param DeployedAppResource deployed_app:
        :return:
        """
        internal_service, external_service = self._get_internal_external_services_set(
            services
        )

        data = [
            VmDetailsProperty(key="Image", value=self._get_image(deployment)),
            VmDetailsProperty(
                key="Replicas", value=self._get_replicas(deployment, deployed_app)
            ),
            VmDetailsProperty(
                key="Ready Replicas", value=self._get_ready_replicas(deployment)
            ),
            VmDetailsProperty(
                key="Internal IP", value=self.get_internal_ip(internal_service)
            ),
            VmDetailsProperty(
                key="Internal Ports", value=self._get_service_ports(internal_service)
            ),
            VmDetailsProperty(
                key="External IP", value=self.get_external_ip(external_service)
            ),
            VmDetailsProperty(
                key="External Ports",
                value=self._get_external_service_ports(external_service),
            ),
        ]

        return data

    def _get_internal_external_services_set(self, services):
        if services:
            internal_service = first_or_default(
                lambda x: x.metadata.labels.get(TagsService.INTERNAL_SERVICE, False),
                services,
            )

            external_service = first_or_default(
                lambda x: x.metadata.labels.get(TagsService.EXTERNAL_SERVICE, False),
                services,
            )

            return internal_service, external_service

        return None, None

    @staticmethod
    def get_internal_ip(internal_service):
        if internal_service:
            return internal_service.spec.cluster_ip
        else:
            return ""

    @staticmethod
    def get_external_ip(external_service):
        if not external_service:
            return ""

        try:
            return ", ".join(
                [x.ip for x in external_service.status.load_balancer.ingress]
            )
        except Exception:
            try:
                return ",".join(
                    [x.hostname for x in external_service.status.load_balancer.ingress]
                )
            except Exception:
                try:
                    return ", ".join(
                        [x.ip for x in external_service.spec.load_balancer_ip]
                    )
                except Exception:
                    return ""

    def _get_service_ports(self, internal_service):
        if internal_service:
            return ", ".join([str(port.port) for port in internal_service.spec.ports])
        else:
            return ""

    def _get_external_service_ports(self, external_service):
        if external_service:
            return ", ".join(
                [
                    "{port}:{node_port}".format(
                        port=str(port.port), node_port=str(port.node_port)
                    )
                    if port.node_port and external_service.spec.type == "NodePort"
                    else str(port.port)
                    for port in external_service.spec.ports
                ]
            )
        else:
            return ""

    def _get_replicas(self, deployment, deployed_app):
        return deployed_app.replicas if deployed_app else deployment.spec.replicas

    def _get_ready_replicas(self, deployment):
        return (
            deployment.status.ready_replicas
            if deployment.status.ready_replicas
            else "0"
        )

    def _get_image(self, deployment):
        images = {c.image for c in deployment.spec.template.spec.containers}
        return ", ".join(images)
