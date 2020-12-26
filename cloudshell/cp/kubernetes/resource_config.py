from cloudshell.shell.standards.core.resource_config_entities import GenericResourceConfig, ResourceAttrRO, \
    PasswordAttrRO


class KubernetesResourceConfig(GenericResourceConfig):
    sandbox_id = None
    config_file_path = ResourceAttrRO("Config File Path", ResourceAttrRO.NAMESPACE.SHELL_NAME)
    aws_access_key_id = PasswordAttrRO("AWS Access Key Id", PasswordAttrRO.NAMESPACE.SHELL_NAME)
    aws_secret_access_key = PasswordAttrRO("AWS Secret Access Key", PasswordAttrRO.NAMESPACE.SHELL_NAME)
    external_service_type = ResourceAttrRO("External Service Type", ResourceAttrRO.NAMESPACE.SHELL_NAME)

    @classmethod
    def from_context(cls, shell_name, context, api=None, supported_os=None):
        instance = super().from_context(shell_name, context, api, supported_os)
        if hasattr(context, "reservation") and context.reservation is not None:
            instance.sandbox_id = context.reservation.reservation_id
        return instance
