"""
Unit tests for authentication service netrc functionality.

Tests token result handling, netrc file operations, and credential management.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from destinepyauth.configs import BaseConfig
from destinepyauth.authentication import AuthenticationService
from destinepyauth.exceptions import AuthenticationError


class TestAuthenticationServiceNetrc:
    """Tests for netrc file writing functionality."""

    def test_netrc_host_extraction_from_redirect_uri(self):
        """Test that netrc_host is extracted from redirect_uri."""
        config = BaseConfig(
            iam_client="test-client",
            iam_redirect_uri="https://example.com/callback",
        )

        with patch("destinepyauth.authentication.KeycloakOpenID", create=True):
            auth_service = AuthenticationService(
                config=config,
                scope="openid",
            )

            assert auth_service.netrc_host == "example.com"

    def test_netrc_host_explicit_parameter(self):
        """Test that explicitly provided netrc_host takes precedence."""
        config = BaseConfig(
            iam_client="test-client",
            iam_redirect_uri="https://example.com/callback",
        )

        with patch("destinepyauth.authentication.KeycloakOpenID", create=True):
            auth_service = AuthenticationService(
                config=config,
                scope="openid",
                netrc_host="custom.host.com",
            )

            assert auth_service.netrc_host == "custom.host.com"

    def test_write_netrc_creates_new_file(self):
        """Test writing netrc creates a new file with correct permissions."""
        config = BaseConfig(iam_client="test-client")

        with patch("destinepyauth.authentication.KeycloakOpenID", create=True):
            with TemporaryDirectory() as tmpdir:
                netrc_path = Path(tmpdir) / ".netrc"
                auth_service = AuthenticationService(
                    config=config,
                    scope="openid",
                    netrc_host="example.com",
                )

                auth_service._write_netrc("test_token_123", netrc_path=netrc_path)

                assert netrc_path.exists()
                content = netrc_path.read_text()
                assert "machine example.com" in content
                assert "login anonymous" in content
                assert "password test_token_123" in content

                # Check file permissions are 600 (owner read/write only)
                import stat

                mode = netrc_path.stat().st_mode
                assert mode & stat.S_IRUSR
                assert mode & stat.S_IWUSR

    def test_write_netrc_updates_existing_entry(self):
        """Test that writing netrc updates existing entry for same host."""
        config = BaseConfig(iam_client="test-client")

        with patch("destinepyauth.authentication.KeycloakOpenID", create=True):
            with TemporaryDirectory() as tmpdir:
                netrc_path = Path(tmpdir) / ".netrc"
                # Create initial netrc with entry
                netrc_path.write_text("machine example.com\n    login anonymous\n    password old_token\n")

                auth_service = AuthenticationService(
                    config=config,
                    scope="openid",
                    netrc_host="example.com",
                )

                auth_service._write_netrc("new_token_456", netrc_path=netrc_path)

                content = netrc_path.read_text()
                assert "password new_token_456" in content
                assert "password old_token" not in content

    def test_write_netrc_no_host_raises_error(self):
        """Test that writing netrc without host configured raises error."""
        config = BaseConfig(iam_client="test-client")

        with patch("destinepyauth.authentication.KeycloakOpenID", create=True):
            auth_service = AuthenticationService(
                config=config,
                scope="openid",
                netrc_host=None,
            )

            with pytest.raises(AuthenticationError, match="no host configured"):
                auth_service._write_netrc("test_token")
