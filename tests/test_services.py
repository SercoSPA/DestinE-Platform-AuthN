"""
Unit tests for service registry and configuration factory.

Tests ServiceRegistry and ConfigurationFactory functionality.
"""

import pytest

from destinepyauth.configs import BaseExchangeConfig
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

    def test_service_config_exists(self):
        """Test checking if service config exists."""
        assert ServiceRegistry.service_config_exists("highway")
        assert ServiceRegistry.service_config_exists("cacheb")
        assert not ServiceRegistry.service_config_exists("nonexistent")

    def test_get_service_config_path(self):
        """Test getting service config path."""
        path = ServiceRegistry.get_service_config_path("highway")
        assert path.exists()
        assert path.name == "highway.yaml"

    def test_get_service_config_path_unknown_service(self):
        """Test that unknown service raises ValueError."""
        with pytest.raises(ValueError, match="Unknown service"):
            ServiceRegistry.get_service_config_path("nonexistent_service")


class TestConfigurationFactory:
    """Tests for configuration factory."""

    def test_load_config_highway(self):
        """Test loading configuration for highway service."""
        config = ConfigurationFactory.load_config("highway")

        assert config.scope == "openid"
        assert config.iam_client == "highway-public"
        assert config.exchange_config is not None
        assert isinstance(config.exchange_config, BaseExchangeConfig)
        assert config.exchange_config.audience == "highway-public"
        assert (
            config.exchange_config.token_url
            == "https://highway.esa.int/sso/auth/realms/highway/protocol/openid-connect/token"
        )

    def test_load_config_cacheb(self):
        """Test loading configuration for cacheb service."""
        config = ConfigurationFactory.load_config("cacheb")

        assert config.scope == "openid offline_access"
        assert config.iam_client == "edh-public"
        assert config.exchange_config is None

    def test_load_config_applies_defaults(self):
        """Test that load_config applies service defaults from YAML."""
        config = ConfigurationFactory.load_config("eden")

        # Defaults from eden.yaml should be applied
        assert config.iam_client == "hda-broker-public"
        assert config.iam_redirect_uri == "https://broker.eden.destine.eu/"

    def test_all_redirect_uris_are_https(self):
        """Test that all service redirect URIs use HTTPS."""
        from urllib.parse import urlparse
        import yaml

        for service in ServiceRegistry.list_services():
            config_path = ServiceRegistry.get_service_config_path(service)
            with open(config_path) as f:
                service_config = yaml.safe_load(f)

            redirect_uri = service_config.get("iam_redirect_uri")
            if redirect_uri:
                parsed = urlparse(redirect_uri)
                assert redirect_uri.startswith("https://"), f"{service} has non-HTTPS redirect URI"
                assert parsed.netloc, f"{service} redirect URI has no hostname"
