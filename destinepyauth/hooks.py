"""Token exchange helper used by service registry."""

import logging
from typing import Dict, Any, Optional

import requests

from destinepyauth.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

# Token exchange grant type per RFC 8693
TOKEN_EXCHANGE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:token-exchange"


def token_exchange(
    *,
    token_url: str,
    subject_token: str,
    client_id: str,
    audience: str,
    subject_issuer: str,
    subject_token_type: str = "urn:ietf:params:oauth:token-type:access_token",
    timeout: int = 10,
) -> str:
    """
    Exchange an OAuth2 access token using the token-exchange grant.

    This is used when a service validates tokens against a different issuer
    than the one used for the initial interactive login.
    """
    data: Dict[str, Any] = {
        "grant_type": TOKEN_EXCHANGE_GRANT_TYPE,
        "subject_token": subject_token,
        "subject_issuer": subject_issuer,
        "subject_token_type": subject_token_type,
        "client_id": client_id,
        "audience": audience,
    }

    logger.debug("Exchanging token via RFC8693")
    logger.debug(f"Token URL: {token_url}")
    logger.debug(f"Client ID: {client_id}")
    logger.debug(f"Audience: {audience}")
    logger.debug(f"Subject issuer: {subject_issuer}")

    response = requests.post(token_url, data=data, timeout=timeout)

    if response.status_code != 200:
        try:
            error_data = response.json()
            error_msg = error_data.get("error_description", error_data.get("error", "Unknown"))
        except Exception:
            error_msg = response.text[:200]
        raise AuthenticationError(f"Exchange failed: {error_msg}")

    result: Dict[str, Any] = response.json()
    exchanged_token: Optional[str] = result.get("access_token")
    if not exchanged_token:
        raise AuthenticationError("No access token in exchange response")

    return exchanged_token
