"""
Unit tests for authentication service netrc functionality.

Tests token result handling, netrc file operations, and credential management.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

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


class TestAuthenticationServiceLogin2FA:
    """Tests for login flow, including OTP/2FA branch."""

    def _make_response(
        self, status_code: int, content: str = "", headers: dict | None = None
    ) -> requests.Response:
        resp = requests.Response()
        resp.status_code = status_code
        resp._content = content.encode("utf-8")
        resp.headers = headers or {}
        return resp

    def test_login_without_otp_uses_redirect(self):
        config = BaseConfig(
            iam_url="https://auth.example",
            iam_realm="desp",
            iam_client="client",
            iam_redirect_uri="https://app.example/callback",
        )
        svc = AuthenticationService(config=config, scope="openid")

        login_resp = self._make_response(
            302,
            headers={"Location": "https://app.example/callback?code=abc123"},
        )

        svc._submit_otp = MagicMock()

        with patch.object(svc, "_get_credentials", return_value=("u", "p")):
            with patch.object(svc, "_get_auth_url_action", return_value="https://auth.example/login"):
                with patch.object(svc, "_perform_login", return_value=login_resp):
                    with patch.object(
                        svc,
                        "_exchange_code_for_token",
                        return_value={"access_token": "at", "refresh_token": "rt"},
                    ):
                        with patch.object(svc, "_verify_and_decode", return_value=None):
                            result = svc.login()

        assert result.access_token == "at"
        assert result.refresh_token == "rt"
        svc._submit_otp.assert_not_called()

    def test_login_with_otp_challenge_submits_otp(self):
        config = BaseConfig(
            iam_url="https://auth.example",
            iam_realm="desp",
            iam_client="client",
            iam_redirect_uri="https://app.example/callback",
        )
        svc = AuthenticationService(config=config, scope="openid")

        otp_page = """
        <html><body>
          <form action='https://auth.example/otp-action'>
            <input type='text' name='otp'/>
          </form>
        </body></html>
        """.strip()

        login_resp = self._make_response(200, content=otp_page)
        otp_resp = self._make_response(
            302,
            headers={"Location": "https://app.example/callback?code=code-from-otp"},
        )

        svc._submit_otp = MagicMock(return_value=otp_resp)

        with patch.object(svc, "_get_credentials", return_value=("u", "p")):
            with patch.object(svc, "_get_auth_url_action", return_value="https://auth.example/login"):
                with patch.object(svc, "_perform_login", return_value=login_resp):
                    with patch.object(
                        svc,
                        "_exchange_code_for_token",
                        return_value={"access_token": "at", "refresh_token": "rt"},
                    ):
                        with patch.object(svc, "_verify_and_decode", return_value={"sub": "x"}):
                            result = svc.login(otp="123456")

        assert result.access_token == "at"
        assert result.refresh_token == "rt"
        assert result.decoded == {"sub": "x"}
        svc._submit_otp.assert_called_once()
        args, _kwargs = svc._submit_otp.call_args
        assert args[0] == "https://auth.example/otp-action"
        assert args[1] == "otp"
        assert args[2] == "123456"

    def test_login_with_otp_challenge_prompts_if_missing(self):
        config = BaseConfig(
            iam_url="https://auth.example",
            iam_realm="desp",
            iam_client="client",
            iam_redirect_uri="https://app.example/callback",
        )
        svc = AuthenticationService(config=config, scope="openid")

        otp_page = """
        <html><body>
          <form action='https://auth.example/otp-action'>
            <input type='text' name='otp'/>
          </form>
        </body></html>
        """.strip()

        login_resp = self._make_response(200, content=otp_page)
        otp_resp = self._make_response(
            302,
            headers={"Location": "https://app.example/callback?code=code-from-otp"},
        )

        svc._submit_otp = MagicMock(return_value=otp_resp)

        with patch.object(svc, "_get_credentials", return_value=("u", "p")):
            with patch.object(svc, "_get_auth_url_action", return_value="https://auth.example/login"):
                with patch.object(svc, "_perform_login", return_value=login_resp):
                    with patch("destinepyauth.authentication.getpass.getpass", return_value="654321"):
                        with patch.object(
                            svc,
                            "_exchange_code_for_token",
                            return_value={"access_token": "at", "refresh_token": "rt"},
                        ):
                            with patch.object(svc, "_verify_and_decode", return_value=None):
                                _ = svc.login()

        svc._submit_otp.assert_called_once()
        args, _kwargs = svc._submit_otp.call_args
        assert args[2] == "654321"
