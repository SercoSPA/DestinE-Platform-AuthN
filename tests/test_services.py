"""
Unit tests for service registry and configuration factory.

Tests ServiceRegistry and ConfigurationFactory functionality.
"""

import pytest
from unittest.mock import MagicMock, patch

from destinepyauth.configs import BaseConfig
from destinepyauth.services import ServiceRegistry, ConfigurationFactory


class TestServiceRegistry:
    """Tests for service registry."""

    def test_list_services(self):
        """Test listing available services."""
        services = ServiceRegistry.list_services()
        assert isinstance(services, list)
        assert "highway" in services
        assert "cacheb" in services
        assert "eden" in services

    def test_get_service_info_highway(self):
        """Test getting service info for highway."""
        info = ServiceRegistry.get_service_info("highway")
        assert "scope" in info
        assert "defaults" in info
        assert info["defaults"]["iam_client"] == "highway-public"
        assert "post_auth_hook" in info

    def test_get_service_info_cacheb(self):
        """Test getting service info for cacheb."""
        info = ServiceRegistry.get_service_info("cacheb")
        assert info["scope"] == "openid offline_access"
        assert info["defaults"]["iam_client"] == "edh-public"
        assert "post_auth_hook" not in info

    def test_get_service_info_unknown_service(self):
        """Test that unknown service raises ValueError."""
        with pytest.raises(ValueError, match="Unknown service"):
            ServiceRegistry.get_service_info("nonexistent_service")


class TestConfigurationFactory:
    """Tests for configuration factory."""

    @patch("destinepyauth.services.Conflator")
    def test_load_config_highway(self, mock_conflator):
        """Test loading configuration for highway service."""
        mock_config = BaseConfig()
        mock_conflator_instance = MagicMock()
        mock_conflator_instance.load.return_value = mock_config
        mock_conflator.return_value = mock_conflator_instance

        config, scope, hook = ConfigurationFactory.load_config("highway")

        assert scope == "openid"
        assert config.iam_client == "highway-public"
        assert hook is not None

    @patch("destinepyauth.services.Conflator")
    def test_load_config_cacheb(self, mock_conflator):
        """Test loading configuration for cacheb service."""
        mock_config = BaseConfig()
        mock_conflator_instance = MagicMock()
        mock_conflator_instance.load.return_value = mock_config
        mock_conflator.return_value = mock_conflator_instance

        config, scope, hook = ConfigurationFactory.load_config("cacheb")

        assert scope == "openid offline_access"
        assert config.iam_client == "edh-public"
        assert hook is None

    @patch("destinepyauth.services.Conflator")
    def test_load_config_applies_defaults(self, mock_conflator):
        """Test that load_config applies service defaults."""
        mock_config = BaseConfig(iam_client=None, iam_redirect_uri=None)
        mock_conflator_instance = MagicMock()
        mock_conflator_instance.load.return_value = mock_config
        mock_conflator.return_value = mock_conflator_instance

        config, _, _ = ConfigurationFactory.load_config("eden")

        # Defaults should be applied
        assert config.iam_client == "hda-broker-public"
        assert config.iam_redirect_uri == "https://broker.eden.destine.eu/"

    def test_all_redirect_uris_are_https(self):
        """Test that all service redirect URIs use HTTPS."""
        from urllib.parse import urlparse

        for service in ServiceRegistry.list_services():
            info = ServiceRegistry.get_service_info(service)
            redirect_uri = info["defaults"]["iam_redirect_uri"]
            parsed = urlparse(redirect_uri)

            assert redirect_uri.startswith("https://"), f"{service} has non-HTTPS redirect URI"
            assert parsed.netloc, f"{service} redirect URI has no hostname"
