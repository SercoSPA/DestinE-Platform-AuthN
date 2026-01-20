"""Authentication library for DESP (Destination Earth Service Platform)."""

import logging

from destinepyauth.get_token import get_token
from destinepyauth.authentication import AuthenticationService, TokenResult
from destinepyauth.exceptions import AuthenticationError

__all__ = [
    "get_token",
    "TokenResult",
    "AuthenticationService",
    "AuthenticationError",
]

# Ensure library doesn't configure logging for the application.
# Applications (including notebooks) should configure logging.
logging.getLogger(__name__).addHandler(logging.NullHandler())
