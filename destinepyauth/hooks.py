"""
Service-specific hooks for token exchange and post-authentication processing.
"""

import logging
from typing import Dict, Any

import requests

from destinepyauth.configs import BaseConfig
from destinepyauth.exceptions import handle_http_errors, AuthenticationError

logger = logging.getLogger(__name__)

# Highway service constants
HIGHWAY_TOKEN_URL = "https://highway.esa.int/sso/auth/realms/highway/protocol/openid-connect/token"
HIGHWAY_AUDIENCE = "highway-public"
HIGHWAY_ISSUER = "DESP_IAM_PROD"


@handle_http_errors("Highway token exchange failed")
def highway_token_exchange(access_token: str, config: BaseConfig) -> str:
    """
    Exchange a DESP access token for a Highway access token.

    Args:
        access_token: The DESP access token to exchange.
        config: Configuration containing client credentials.

    Returns:
        The Highway access token string.

    Raises:
        AuthenticationError: If the token exchange fails.
    """
    data: Dict[str, Any] = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token": access_token,
        "subject_issuer": HIGHWAY_ISSUER,
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "client_id": config.iam_client,
        "audience": HIGHWAY_AUDIENCE,
    }

    logger.debug("Exchanging DESP token for HIGHWAY token...")
    logger.debug(f"Client ID: {config.iam_client}")

    response = requests.post(HIGHWAY_TOKEN_URL, data=data, timeout=10)

    if response.status_code != 200:
        try:
            error_data = response.json()
            error_msg = error_data.get("error_description", error_data.get("error", "Unknown"))
        except Exception:
            error_msg = response.text[:100]
        raise AuthenticationError(f"Exchange failed: {error_msg}")

    result: Dict[str, Any] = response.json()
    highway_token = result.get("access_token")

    if not highway_token:
        raise AuthenticationError("No access token in response")

    logger.info("Token exchange successful")
    return highway_token
