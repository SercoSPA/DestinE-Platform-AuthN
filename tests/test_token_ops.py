"""
Unit tests for token exchange and verification logic.

Focused tests that verify error handling branches and core logic
in _exchange_token and _verify_and_decode methods.
"""

import pytest
from unittest.mock import MagicMock, patch

from destinepyauth.authentication import AuthenticationService
from destinepyauth.configs import BaseConfig, BaseExchangeConfig
from destinepyauth.exceptions import AuthenticationError


class TestTokenExchange:
    """Tests for _exchange_token RFC 8693 flow."""

    def test_exchange_fails_when_no_config_provided(self):
        """Test that _exchange_token raises error when exchange_config is None."""
        config = BaseConfig(iam_client="test-client")  # No exchange_config
        auth_service = AuthenticationService(config=config)

        with pytest.raises(AuthenticationError, match="No exchange configuration provided"):
            auth_service._exchange_token("some_token")

    def test_exchange_fails_on_non_200_response(self):
        """Test that non-200 responses raise AuthenticationError with error details."""
        exchange_config = BaseExchangeConfig(
            token_url="https://exchange.example.com/token",
            client_id="client",
            audience="audience",
            subject_issuer="issuer",
        )
        config = BaseConfig(iam_client="test", exchange_config=exchange_config)
        auth_service = AuthenticationService(config=config)

        # Mock a 400 error response with JSON error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "invalid_grant", "error_description": "Token expired"}

        with patch.object(auth_service.session, "post", return_value=mock_response):
            with pytest.raises(AuthenticationError, match="Exchange failed: Token expired"):
                auth_service._exchange_token("expired_token")

    def test_exchange_fails_when_access_token_missing(self):
        """Test that 200 response without access_token raises error."""
        exchange_config = BaseExchangeConfig(
            token_url="https://exchange.example.com/token",
            client_id="client",
            audience="audience",
            subject_issuer="issuer",
        )
        config = BaseConfig(iam_client="test", exchange_config=exchange_config)
        auth_service = AuthenticationService(config=config)

        # Mock 200 response but missing access_token field
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token_type": "Bearer"}  # No access_token!

        with patch.object(auth_service.session, "post", return_value=mock_response):
            with pytest.raises(AuthenticationError, match="No access token in exchange response"):
                auth_service._exchange_token("original_token")

    def test_exchange_success_returns_access_token(self):
        """Test that successful exchange returns the access_token from response."""
        exchange_config = BaseExchangeConfig(
            token_url="https://exchange.example.com/token",
            client_id="client",
            audience="audience",
            subject_issuer="issuer",
        )
        config = BaseConfig(iam_client="test", exchange_config=exchange_config)
        auth_service = AuthenticationService(config=config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "new_exchanged_token_xyz"}

        with patch.object(auth_service.session, "post", return_value=mock_response):
            result = auth_service._exchange_token("original_token")
            assert result == "new_exchanged_token_xyz"


class TestTokenVerification:
    """Tests for _verify_and_decode JWT verification."""

    def test_verify_returns_none_on_decode_failure(self):
        """Test that verification returns None when JWT decode/validation fails."""
        config = BaseConfig(iam_client="test")
        auth_service = AuthenticationService(config=config)

        # Mock the dependencies to make authlib_jwt.decode raise an exception
        with patch("destinepyauth.authentication.requests.get") as mock_get:
            # Setup OIDC config and JWKS responses
            mock_oidc_response = MagicMock()
            mock_oidc_response.json.return_value = {"jwks_uri": "https://auth.example.com/jwks"}

            mock_jwks_response = MagicMock()
            mock_jwks_response.json.return_value = {"keys": []}

            mock_get.side_effect = [mock_oidc_response, mock_jwks_response]

            with patch(
                "destinepyauth.authentication.authlib_jwt.decode", side_effect=Exception("Invalid signature")
            ):
                # Use a real-looking JWT format (3 base64 parts)
                fake_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2V5In0.eyJpc3MiOiJodHRwczovL2F1dGguZXhhbXBsZS5jb20ifQ.fake_sig"  # pragma: allowlist secret
                result = auth_service._verify_and_decode(fake_token)
                assert result is None

    def test_verify_returns_claims_on_success(self):
        """Test that successful verification returns decoded claims."""
        config = BaseConfig(iam_client="test")
        auth_service = AuthenticationService(config=config)

        expected_claims = {
            "sub": "user@example.com",
            "iss": "https://auth.example.com",
            "exp": 1234567890,
            "iat": 1234567800,
        }

        with patch("destinepyauth.authentication.requests.get") as mock_get:
            # Setup OIDC config and JWKS responses
            mock_oidc_response = MagicMock()
            mock_oidc_response.json.return_value = {"jwks_uri": "https://auth.example.com/jwks"}

            mock_jwks_response = MagicMock()
            mock_jwks_response.json.return_value = {"keys": []}

            mock_get.side_effect = [mock_oidc_response, mock_jwks_response]

            # Mock successful decode and validation - make it dict-like
            mock_claims = MagicMock()
            mock_claims.validate = MagicMock()
            # Make dict(mock_claims) work by implementing keys() and __getitem__
            mock_claims.keys.return_value = expected_claims.keys()
            mock_claims.__getitem__ = lambda self, key: expected_claims[key]

            with patch("destinepyauth.authentication.authlib_jwt.decode", return_value=mock_claims):
                fake_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2V5In0.eyJpc3MiOiJodHRwczovL2F1dGguZXhhbXBsZS5jb20ifQ.fake_sig"  # pragma: allowlist secret
                result = auth_service._verify_and_decode(fake_token)
                assert result == expected_claims
