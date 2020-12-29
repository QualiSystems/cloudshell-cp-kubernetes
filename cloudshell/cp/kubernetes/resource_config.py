from cloudshell.shell.standards.core.resource_config_entities import GenericResourceConfig, ResourceAttrRO


class KubernetesResourceConfig(GenericResourceConfig):
    sandbox_id = None
    config_file_path = ResourceAttrRO("Config File Path", ResourceAttrRO.NAMESPACE.SHELL_NAME)
    # aws_access_key_id = PasswordAttrRO("AWS Access Key Id", PasswordAttrRO.NAMESPACE.SHELL_NAME)
    # aws_secret_access_key = PasswordAttrRO("AWS Secret Access Key", PasswordAttrRO.NAMESPACE.SHELL_NAME)
    aws_cp_resource_name = ResourceAttrRO("AWS CP Resource Name", ResourceAttrRO.NAMESPACE.SHELL_NAME)
    external_service_type = ResourceAttrRO("External Service Type", ResourceAttrRO.NAMESPACE.SHELL_NAME)

    def _extract_resource_attribute(self, resource_name, attribute_name):
        cs_api = self.api
        """
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cs_api:
        """
        aws_resource = cs_api.GetResourceDetails(resource_name)
        if not aws_resource:
            raise Exception("Unable to find a resource with name {}".format(resource_name))
        result = list(filter(lambda x: x.Name == attribute_name, aws_resource.ResourceAttributes))
        if not result:
            raise Exception("The resource {} does not have the attribute with name {}".format(resource_name, attribute_name))
        return result[0].Value

    @property
    def aws_access_key_id(self):
        if not self.aws_cp_resource_name:
            return None
        return self.api.DecryptPassword(
            self._extract_resource_attribute(self.aws_cp_resource_name, 'AWS Access Key ID')).Value

    @property
    def aws_secret_access_key(self):
        if not self.aws_cp_resource_name:
            return None
        return self.api.DecryptPassword(
            self._extract_resource_attribute(self.aws_cp_resource_name, 'AWS Secret Access Key')).Value

    @classmethod
    def from_context(cls, shell_name, context, api=None, supported_os=None):
        instance = super().from_context(shell_name, context, api, supported_os)
        if hasattr(context, "reservation") and context.reservation is not None:
            instance.sandbox_id = context.reservation.reservation_id
        return instance
