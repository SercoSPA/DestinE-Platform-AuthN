"""
Unit tests for get_token high-level API.

Tests core behavior: return values, logging, and error propagation.
"""

import logging
import pytest
from unittest.mock import patch, MagicMock, ANY

from destinepyauth.get_token import get_token
from destinepyauth.authentication import TokenResult
from destinepyauth.exceptions import AuthenticationError


class TestGetToken:
    """Tests for get_token() function."""

    def test_get_token_returns_token_result_when_not_writing_netrc(self):
        """Test that get_token returns TokenResult when write_netrc=False."""
        mock_result = TokenResult(access_token="test_token_123")

        with patch("destinepyauth.get_token.ConfigurationFactory.load_config") as mock_load_config:
            with patch("destinepyauth.get_token.AuthenticationService") as mock_auth_class:
                mock_auth = MagicMock()
                mock_auth.login.return_value = mock_result
                mock_auth_class.return_value = mock_auth

                result = get_token("highway", write_netrc=False)

                assert result is mock_result
                assert result.access_token == "test_token_123"
                mock_auth_class.assert_called_once_with(config=ANY, service_name="highway")
                mock_load_config.assert_called_once_with("highway", config_path=None)

    def test_get_token_returns_none_when_writing_netrc(self):
        """Test that get_token returns None when write_netrc=True to avoid token exposure."""
        with patch("destinepyauth.get_token.ConfigurationFactory.load_config"):
            with patch("destinepyauth.get_token.AuthenticationService") as mock_auth_class:
                mock_auth = MagicMock()
                mock_auth.login.return_value = TokenResult(access_token="token")
                mock_auth_class.return_value = mock_auth

                result = get_token("highway", write_netrc=True)

                assert result is None
                mock_auth_class.assert_called_once_with(config=ANY, service_name="highway")

    def test_get_token_configures_logging_level(self):
        """Test that get_token sets library logger level based on verbose flag."""
        with patch("destinepyauth.get_token.ConfigurationFactory.load_config"):
            with patch("destinepyauth.get_token.AuthenticationService") as mock_auth_class:
                mock_auth = MagicMock()
                mock_auth.login.return_value = TokenResult(access_token="token")
                mock_auth_class.return_value = mock_auth

                # Test verbose=False sets INFO
                get_token("highway", verbose=False)
                logger = logging.getLogger("destinepyauth")
                assert logger.level == logging.INFO

                # Test verbose=True sets DEBUG
                get_token("highway", verbose=True)
                assert logger.level == logging.DEBUG

    def test_get_token_propagates_authentication_error(self):
        """Test that AuthenticationError is propagated from login()."""
        with patch("destinepyauth.get_token.ConfigurationFactory.load_config"):
            with patch("destinepyauth.get_token.AuthenticationService") as mock_auth_class:
                mock_auth = MagicMock()
                mock_auth.login.side_effect = AuthenticationError("Login failed")
                mock_auth_class.return_value = mock_auth

                with pytest.raises(AuthenticationError, match="Login failed"):
                    get_token("highway")

    def test_get_token_passes_custom_config_path(self):
        """Test that get_token forwards custom config path to ConfigurationFactory."""
        config_path = "/tmp/custom_service.yaml"

        with patch("destinepyauth.get_token.ConfigurationFactory.load_config") as mock_load_config:
            with patch("destinepyauth.get_token.AuthenticationService") as mock_auth_class:
                mock_auth = MagicMock()
                mock_auth.login.return_value = TokenResult(access_token="token")
                mock_auth_class.return_value = mock_auth

                get_token(service="custom-service", config_path=config_path)

                mock_load_config.assert_called_once_with("custom-service", config_path=config_path)

    def test_get_token_allows_config_path_without_service(self):
        """Test that service can be inferred from config file name when omitted."""
        config_path = "/tmp/myservice.yaml"

        with patch("destinepyauth.get_token.ConfigurationFactory.load_config") as mock_load_config:
            with patch("destinepyauth.get_token.AuthenticationService") as mock_auth_class:
                mock_auth = MagicMock()
                mock_auth.login.return_value = TokenResult(access_token="token")
                mock_auth_class.return_value = mock_auth

                get_token(config_path=config_path)

                mock_load_config.assert_called_once_with("myservice", config_path=config_path)
                mock_auth_class.assert_called_once_with(config=ANY, service_name="myservice")

    def test_get_token_requires_service_or_config_path(self):
        """Test that get_token raises when neither service nor config_path are provided."""
        with pytest.raises(ValueError, match="Either service or config_path must be provided"):
            get_token()
