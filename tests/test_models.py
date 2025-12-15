"""
Unit tests for data models and configuration.

Tests TokenResult, BaseConfig, and configuration-related functionality.
"""

from destinepyauth.configs import BaseConfig
from destinepyauth.authentication import TokenResult


class TestTokenResult:
    """Tests for TokenResult dataclass."""

    def test_token_result_creation(self):
        """Test creating a TokenResult with access token."""
        result = TokenResult(access_token="test_token_123")
        assert result.access_token == "test_token_123"
        assert result.refresh_token is None
        assert result.decoded is None

    def test_token_result_with_all_fields(self):
        """Test TokenResult with all fields populated."""
        decoded_payload = {"sub": "user123", "exp": 1234567890}
        result = TokenResult(
            access_token="access_123",
            refresh_token="refresh_456",
            decoded=decoded_payload,
        )
        assert result.access_token == "access_123"
        assert result.refresh_token == "refresh_456"
        assert result.decoded == decoded_payload

    def test_token_result_str_representation(self):
        """Test that TokenResult can be used as string (returns token)."""
        result = TokenResult(access_token="my_token")
        assert str(result) == "my_token"


class TestBaseConfig:
    """Tests for configuration model."""

    def test_config_with_defaults(self):
        """Test creating config with default values."""
        config = BaseConfig()
        assert config.iam_url == "https://auth.destine.eu"
        assert config.iam_realm == "desp"
        assert config.user is None
        assert config.password is None

    def test_config_with_custom_values(self):
        """Test creating config with custom values."""
        config = BaseConfig(
            user="testuser",
            password="testpass",
            iam_url="https://custom.auth.com",
        )
        assert config.user == "testuser"
        assert config.password == "testpass"
        assert config.iam_url == "https://custom.auth.com"
        assert config.iam_realm == "desp"  # default unchanged
