from unittest import TestCase
from unittest.mock import Mock, patch

from cloudshell.cp.kubernetes.resource_config import KubernetesResourceConfig


class TestResourceConfig(TestCase):
    def setUp(self):
        pass

    @patch(
        "cloudshell.cp.kubernetes.resource_config.GenericResourceConfig.from_context"
    )
    def test_from_context(self, from_context):
        instance_mock = Mock()
        from_context.return_value = instance_mock
        shell_name = Mock()
        context = Mock()
        instance = KubernetesResourceConfig.from_context(shell_name, context)
        self.assertIs(instance_mock, instance)
        from_context.called_once_with(shell_name, context)
