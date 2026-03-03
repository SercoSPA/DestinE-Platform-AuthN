"""
Unit tests for get_token high-level API.

Tests the get_token() function behavior including return values,
logging configuration, and error propagation.
"""

import logging
from unittest.mock import patch, MagicMock

from destinepyauth.get_token import get_token
from destinepyauth.authentication import TokenResult


class TestGetToken:
    """Tests for get_token() function."""

    def test_get_token_returns_token_result(self):
        """Test that get_token returns TokenResult when write_netrc=False."""
        mock_result = TokenResult(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            decoded={"sub": "user@example.com"},
        )

        with patch("destinepyauth.get_token.ConfigurationFactory.load_config") as mock_config:
            with patch("destinepyauth.get_token.AuthenticationService") as mock_auth_class:
                mock_auth_instance = MagicMock()
                mock_auth_instance.login.return_value = mock_result
                mock_auth_class.return_value = mock_auth_instance

                result = get_token("highway", write_netrc=False)

                assert result is mock_result
                mock_config.assert_called_once_with("highway")
                mock_auth_instance.login.assert_called_once_with(write_netrc=False)

    def test_get_token_returns_none_when_write_netrc_true(self):
        """Test that get_token returns None when write_netrc=True."""
        mock_result = TokenResult(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
        )

        with patch("destinepyauth.get_token.ConfigurationFactory.load_config"):
            with patch("destinepyauth.get_token.AuthenticationService") as mock_auth_class:
                mock_auth_instance = MagicMock()
                mock_auth_instance.login.return_value = mock_result
                mock_auth_class.return_value = mock_auth_instance

                result = get_token("highway", write_netrc=True)

                assert result is None
                mock_auth_instance.login.assert_called_once_with(write_netrc=True)

    def test_get_token_sets_logger_to_info_by_default(self):
        """Test that get_token sets library logger to INFO level when verbose=False."""
        with patch("destinepyauth.get_token.ConfigurationFactory.load_config"):
            with patch("destinepyauth.get_token.AuthenticationService") as mock_auth_class:
                mock_auth_instance = MagicMock()
                mock_auth_instance.login.return_value = TokenResult(access_token="token")
                mock_auth_class.return_value = mock_auth_instance

                get_token("highway", verbose=False)

                logger = logging.getLogger("destinepyauth")
                assert logger.level == logging.INFO

    def test_get_token_sets_logger_to_debug_when_verbose_true(self):
        """Test that get_token sets library logger to DEBUG level when verbose=True."""
        with patch("destinepyauth.get_token.ConfigurationFactory.load_config"):
            with patch("destinepyauth.get_token.AuthenticationService") as mock_auth_class:
                mock_auth_instance = MagicMock()
                mock_auth_instance.login.return_value = TokenResult(access_token="token")
                mock_auth_class.return_value = mock_auth_instance

                get_token("highway", verbose=True)

                logger = logging.getLogger("destinepyauth")
                assert logger.level == logging.DEBUG
