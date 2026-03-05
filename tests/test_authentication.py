"""
Unit tests for authentication service netrc functionality.

Tests netrc file operations which are a key feature of this library.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import stat
import json
from unittest.mock import MagicMock
import requests

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

    def test_write_polytopeapirc_creates_file(self):
        """Test writing Polytope token file creates expected JSON payload."""
        config = BaseConfig(iam_client="polytope-api-public")

        with TemporaryDirectory() as tmpdir:
            outpath = Path(tmpdir) / ".polytopeapirc"
            auth_service = AuthenticationService(config=config)

            auth_service._write_polytopeapirc("refresh_token_123", outpath=outpath)

            assert outpath.exists()
            payload = json.loads(outpath.read_text())
            assert payload == {"user_key": "refresh_token_123"}

            mode = outpath.stat().st_mode
            assert mode & stat.S_IRUSR
            assert mode & stat.S_IWUSR

    def test_login_writes_polytopeapirc_by_default(self, monkeypatch):
        """Test that Polytope login writes refresh token file by default."""
        config = BaseConfig(
            iam_client="polytope-api-public",
            iam_redirect_uri="https://polytope.example/callback",
        )
        with TemporaryDirectory() as tmpdir:
            monkeypatch.setattr(Path, "home", lambda: Path(tmpdir))

            auth_service = AuthenticationService(config=config, service_name="polytope")

            auth_service._get_credentials = MagicMock(return_value=("user", "pass"))
            auth_service._get_auth_url_action = MagicMock(return_value="https://auth.example/login")

            login_response = MagicMock()
            login_response.status_code = 302
            login_response.headers = {"Location": "https://polytope.example/callback?code=abc123"}
            auth_service._perform_login = MagicMock(return_value=login_response)

            auth_service._exchange_code_for_token = MagicMock(
                return_value={"access_token": "access_123", "refresh_token": "refresh_123"}
            )
            auth_service._verify_and_decode = MagicMock(return_value={"sub": "user"})

            result = auth_service.login(write_netrc=False)

            outpath = Path(tmpdir) / ".polytopeapirc"
            assert outpath.exists()
            payload = json.loads(outpath.read_text())
            assert payload == {"user_key": "refresh_123"}

            mode = outpath.stat().st_mode
            assert mode & stat.S_IRUSR
            assert mode & stat.S_IWUSR

            assert result.access_token == "access_123"
            assert result.refresh_token == "refresh_123"


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

    def test_submit_otp_posts_correct_data(self):
        """Test that OTP submission POSTs with correct form data."""

        config = BaseConfig(iam_client="test")
        auth_service = AuthenticationService(config=config)

        mock_response = MagicMock()
        mock_response.status_code = 302
        mock_response.headers = {"Location": "https://example.com/success"}

        # Patch the session's post method
        auth_service.session.post = MagicMock(return_value=mock_response)

        result = auth_service._submit_otp("https://auth.example/otp-submit", "123456")

        # Verify POST was called with correct URL and data
        auth_service.session.post.assert_called_once_with(
            "https://auth.example/otp-submit",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"otp": "123456", "login": "Sign In"},
            allow_redirects=False,
            timeout=10,
        )

        assert result == mock_response

    def test_submit_otp_handles_http_errors(self):
        """Test that OTP submission handles HTTP errors appropriately."""

        config = BaseConfig(iam_client="test")
        auth_service = AuthenticationService(config=config)

        # Simulate HTTP error on the session
        auth_service.session.post = MagicMock(side_effect=requests.Timeout("Request timed out"))

        with pytest.raises(AuthenticationError, match="Failed to submit OTP"):
            auth_service._submit_otp("https://auth.example/otp", "123456")
