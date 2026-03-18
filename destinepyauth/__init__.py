"""Authentication library for DESP (Destination Earth Service Platform)."""

import logging
from importlib.metadata import PackageNotFoundError, version

from destinepyauth.get_token import get_token
from destinepyauth.authentication import AuthenticationService, TokenResult
from destinepyauth.exceptions import AuthenticationError

try:
    __version__ = version("destinepyauth")
except PackageNotFoundError:
    # Fallback for local source usage where package metadata is unavailable.
    __version__ = "0+unknown"

__all__ = [
    "get_token",
    "TokenResult",
    "AuthenticationService",
    "AuthenticationError",
    "__version__",
]

# Ensure library doesn't configure logging for the application.
# Applications (including notebooks) should configure logging.
logging.getLogger(__name__).addHandler(logging.NullHandler())
