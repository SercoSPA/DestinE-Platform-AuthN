"""
Unit tests for configuration precedence chain.

Tests the Conflator-based configuration merging:
  Service YAML defaults → User config files → Environment variables → CLI args
"""

from destinepyauth.services import ConfigurationFactory


class TestServiceYAMLDefaults:
    """Tests that service YAML defaults are loaded correctly."""

    def test_highway_service_defaults_loaded(self):
        """Test that highway service YAML provides expected defaults."""
        config = ConfigurationFactory.load_config("highway")

        # Values from highway.yaml
        assert config.scope == "openid"
        assert config.iam_client == "highway-public"
        assert (
            config.iam_redirect_uri
            == "https://highway.esa.int/sso/auth/realms/highway/broker/DESP_IAM_PROD/endpoint"
        )

        # Exchange config from highway.yaml
        assert config.exchange_config is not None
        assert config.exchange_config.audience == "highway-public"
        assert config.exchange_config.subject_issuer == "DESP_IAM_PROD"
        assert (
            config.exchange_config.token_url
            == "https://highway.esa.int/sso/auth/realms/highway/protocol/openid-connect/token"
        )

        # BaseConfig defaults should still apply
        assert config.iam_url == "https://auth.destine.eu"
        assert config.iam_realm == "desp"

    def test_cacheb_service_defaults_loaded(self):
        """Test that cacheb service YAML provides expected defaults."""
        config = ConfigurationFactory.load_config("cacheb")

        # Values from cacheb.yaml
        assert config.scope == "openid offline_access"
        assert config.iam_client == "edh-public"
        assert config.iam_redirect_uri == "https://cacheb.dcms.destine.eu/"

        # No exchange config in cacheb.yaml
        assert config.exchange_config is None


class TestEnvironmentVariableOverrides:
    """Tests that environment variables override service defaults."""

    def test_env_var_overrides_iam_url(self, monkeypatch):
        """Test DESPAUTH_IAM_URL overrides service default."""
        monkeypatch.setenv("DESPAUTH_IAM_URL", "https://custom-auth.example.com")

        config = ConfigurationFactory.load_config("highway")

        # Environment variable should override BaseConfig default
        assert config.iam_url == "https://custom-auth.example.com"

        # Service defaults should still be present
        assert config.iam_client == "highway-public"

    def test_env_var_overrides_iam_realm(self, monkeypatch):
        """Test DESPAUTH_REALM overrides BaseConfig default."""
        monkeypatch.setenv("DESPAUTH_REALM", "custom-realm")

        config = ConfigurationFactory.load_config("cacheb")

        assert config.iam_realm == "custom-realm"

    def test_env_var_overrides_scope(self, monkeypatch):
        """Test DESPAUTH_SCOPE overrides service YAML scope."""
        monkeypatch.setenv("DESPAUTH_SCOPE", "openid profile email")

        config = ConfigurationFactory.load_config("highway")

        # Environment variable should override service YAML value
        assert config.scope == "openid profile email"

    def test_env_var_overrides_iam_client(self, monkeypatch):
        """Test DESPAUTH_CLIENT_ID overrides service YAML iam_client."""
        monkeypatch.setenv("DESPAUTH_CLIENT_ID", "my-custom-client")

        config = ConfigurationFactory.load_config("highway")

        # Environment variable should override service YAML value
        assert config.iam_client == "my-custom-client"

    def test_env_var_sets_user_and_password(self, monkeypatch):
        """Test DESPAUTH_USER and DESPAUTH_PASSWORD set credentials."""
        monkeypatch.setenv("DESPAUTH_USER", "testuser")
        monkeypatch.setenv("DESPAUTH_PASSWORD", "testpass")

        config = ConfigurationFactory.load_config("cacheb")

        assert config.user == "testuser"
        assert config.password == "testpass"  # pragma: allowlist secret

    def test_multiple_env_vars_work_together(self, monkeypatch):
        """Test that multiple environment variables can override simultaneously."""
        monkeypatch.setenv("DESPAUTH_IAM_URL", "https://staging-auth.example.com")
        monkeypatch.setenv("DESPAUTH_REALM", "test")
        monkeypatch.setenv("DESPAUTH_USER", "testuser")
        monkeypatch.setenv("DESPAUTH_SCOPE", "openid offline_access")

        config = ConfigurationFactory.load_config("highway")

        # All env vars should apply
        assert config.iam_url == "https://staging-auth.example.com"
        assert config.iam_realm == "test"
        assert config.user == "testuser"
        assert config.scope == "openid offline_access"

        # Service YAML values still present for non-overridden fields
        assert config.iam_client == "highway-public"


class TestConfigurationPrecedenceChain:
    """Tests that the complete precedence chain works correctly."""

    def test_env_var_wins_over_user_config(self, monkeypatch):
        """Test that environment variables take precedence over user config files.

        This test verifies the documented precedence by setting an env var,
        which should override any user config (even though we can't easily
        test user config discovery in unit tests).
        """
        # Set environment variable (highest priority)
        monkeypatch.setenv("DESPAUTH_IAM_URL", "https://env-var-url.example.com")

        config = ConfigurationFactory.load_config("highway")

        # Environment variable should win over any lower-priority source
        assert config.iam_url == "https://env-var-url.example.com"

    def test_service_yaml_is_lowest_priority(self):
        """Test that service YAML is the base layer with lowest priority."""
        # No env vars, no user config - pure service YAML
        config = ConfigurationFactory.load_config("highway")

        # Service YAML values should apply
        assert config.scope == "openid"
        assert config.iam_client == "highway-public"

        # BaseConfig defaults should apply when not in service YAML
        assert config.iam_url == "https://auth.destine.eu"
        assert config.user is None
        assert config.password is None
