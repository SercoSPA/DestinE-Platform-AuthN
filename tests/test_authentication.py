"""
Unit tests for authentication service netrc functionality.

Tests netrc file operations which are a key feature of this library.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import stat
from unittest.mock import MagicMock

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
        auth_service = AuthenticationService(config=config)
        assert auth_service.netrc_host == "example.com"

    def test_netrc_host_explicit_parameter(self):
        """Test that explicitly provided netrc_host takes precedence."""
        config = BaseConfig(
            iam_client="test-client",
            iam_redirect_uri="https://example.com/callback",
        )
        auth_service = AuthenticationService(
            config=config,
            netrc_host="custom.host.com",
        )
        assert auth_service.netrc_host == "custom.host.com"

    def test_write_netrc_creates_new_file(self):
        """Test writing netrc creates a new file with correct permissions."""
        config = BaseConfig(iam_client="test-client")

        with TemporaryDirectory() as tmpdir:
            netrc_path = Path(tmpdir) / ".netrc"
            auth_service = AuthenticationService(
                config=config,
                netrc_host="example.com",
            )

            auth_service._write_netrc("test_token_123", netrc_path=netrc_path)

            assert netrc_path.exists()
            content = netrc_path.read_text()
            assert "machine example.com" in content
            assert "login anonymous" in content
            assert "password test_token_123" in content

            # Check file permissions are 600 (owner read/write only)

            mode = netrc_path.stat().st_mode
            assert mode & stat.S_IRUSR
            assert mode & stat.S_IWUSR

    def test_write_netrc_updates_existing_entry(self):
        """Test that writing netrc updates existing entry for same host."""
        config = BaseConfig(iam_client="test-client")

        with TemporaryDirectory() as tmpdir:
            netrc_path = Path(tmpdir) / ".netrc"
            # Create initial netrc with entry
            netrc_path.write_text("machine example.com\n    login anonymous\n    password old_token\n")

            auth_service = AuthenticationService(
                config=config,
                netrc_host="example.com",
            )

            auth_service._write_netrc("new_token_456", netrc_path=netrc_path)

            content = netrc_path.read_text()
            assert "password new_token_456" in content
            assert "password old_token" not in content

    def test_write_netrc_no_host_raises_error(self):
        """Test that writing netrc without host configured raises error."""
        config = BaseConfig(iam_client="test-client")
        auth_service = AuthenticationService(
            config=config,
            netrc_host=None,
        )

        with pytest.raises(AuthenticationError, match="no host configured"):
            auth_service._write_netrc("test_token")


class TestAuthenticationOTPFlow:
    """Tests for OTP extraction logic."""

    def test_extract_otp_action_from_html(self):
        """Test that OTP form action is extracted from HTML."""
        config = BaseConfig(iam_client="test")
        auth_service = AuthenticationService(config=config)

        otp_html = """
        <html><body>
          <form action='https://auth.example/otp-submit'>
            <input type='text' name='otp'/>
          </form>
        </body></html>
        """

        mock_response = MagicMock()
        mock_response.content.decode.return_value = otp_html

        action_url = auth_service._extract_otp_action(mock_response)
        assert action_url == "https://auth.example/otp-submit"

    def test_extract_otp_action_fails_with_no_form(self):
        """Test that missing OTP form raises AuthenticationError."""
        config = BaseConfig(iam_client="test")
        auth_service = AuthenticationService(config=config)

        html_no_form = "<html><body>No forms here</body></html>"

        mock_response = MagicMock()
        mock_response.content.decode.return_value = html_no_form

        with pytest.raises(AuthenticationError, match="No OTP form found"):
            auth_service._extract_otp_action(mock_response)
