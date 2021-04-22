import re


def get_provider_tag_name(tag_name):
    """Get Provider tag name.

    :param str tag_name:
    :return:
    """
    return "cloudshell-{}".format(tag_name)


class TagsService(object):
    SANDBOX_ID = "SandboxId"

    INTERNAL_PORT_PREFIX = "pi"
    EXTERNAL_PORT_PREFIX = "pe"

    # SERVICES
    INTERNAL_SERVICE = get_provider_tag_name("internal-service")
    EXTERNAL_SERVICE = get_provider_tag_name("external-service")
    SERVICE_APP_NAME = get_provider_tag_name("service-app-name")
    EXTERNAL_SERVICE_POSTFIX = "external"

    @staticmethod
    def get_default_selector(app_name):
        """Default selector.

        :param str app_name:
        :return:
        """
        return get_provider_tag_name("selector-{app_name}".format(app_name=app_name))

    @staticmethod
    def escape_label_value(value):
        """Escape label.

        :param str value:
        """
        return re.sub(r"\s", "_", value)

    def __init__(self, context):
        if not hasattr(context, "reservation") or context.reservation is None:
            raise Exception("Cannot find reservation context.")
        reservation = context.reservation
        self.sandbox_id = reservation.reservation_id
        self.owner = self.escape_label_value(reservation.owner_user)
        self.domain = self.escape_label_value(reservation.domain)
        self.blueprint_name = self.escape_label_value(reservation.environment_name)

    def get_default_labels(self):
        return {
            self.SANDBOX_ID: self.sandbox_id,
            "CreatedBy": "CloudShell",
            "Owner": self.owner,
            "Domain": self.domain,
            "Blueprint": self.blueprint_name,
        }
