"""
Unit tests for configuration precedence chain.

Tests the effective behavior in this package:
  Base YAML config (built-in service or custom config path) + env var overrides.
"""

from destinepyauth.services import ConfigurationFactory


class TestConfigurationPrecedence:
    """Tests for core precedence behavior used by the API/CLI."""

    def test_service_yaml_defaults_loaded(self):
        """Built-in service YAML should provide base config values."""
        config = ConfigurationFactory.load_config("highway")

        assert config.scope == "openid"
        assert config.iam_client == "highway-public"
        assert (
            config.iam_redirect_uri
            == "https://highway.esa.int/sso/auth/realms/highway/broker/DESP_IAM_PROD/endpoint"
        )

        assert config.exchange_config is not None
        assert config.exchange_config.audience == "highway-public"
        assert config.iam_url == "https://auth.destine.eu"
        assert config.iam_realm == "desp"

    def test_env_vars_override_base_config_values(self, monkeypatch):
        """Environment variables should override values loaded from YAML."""
        monkeypatch.setenv("DESPAUTH_IAM_URL", "https://env-var-url.example.com")
        monkeypatch.setenv("DESPAUTH_CLIENT_ID", "my-custom-client")
        monkeypatch.setenv("DESPAUTH_USER", "testuser")
        monkeypatch.setenv("DESPAUTH_PASSWORD", "testpass")

        config = ConfigurationFactory.load_config("highway")

        assert config.iam_url == "https://env-var-url.example.com"
        assert config.iam_client == "my-custom-client"
        assert config.user == "testuser"
        assert config.password == "testpass"  # pragma: allowlist secret
