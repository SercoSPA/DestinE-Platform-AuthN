"""High-level API for DESP authentication."""

import logging
from typing import Optional

from destinepyauth.authentication import AuthenticationService, TokenResult
from destinepyauth.services import ConfigurationFactory


def get_token(
    service: str,
    twofa: bool,
    write_netrc: bool = False,
    verbose: bool = False,
) -> Optional[TokenResult]:
    """
    Authenticate and get an access token for a DESP service.

    Credentials are obtained securely via:
    - Environment variables (DESPAUTH_USER, DESPAUTH_PASSWORD)
    - Interactive prompt with masked password input

    Args:
        service: Service name (e.g., 'highway', 'cacheb', 'eden').
        twofa: If True, use explicit 2FA (OTP) login flow.
        write_netrc: If True, write/update the token in ~/.netrc file.
        verbose: If True, enable DEBUG logging.

    Returns:
        TokenResult containing the access token and decoded payload.
        Returns None if write_netrc=True to prevent token exposure in output.

    Raises:
        AuthenticationError: If authentication fails.
        ValueError: If service name is not recognized.
    """
    # Configure only the library logger (do not change the root logger).
    # Applications (including notebooks) should configure handlers.
    log_level = logging.INFO if not verbose else logging.DEBUG
    logging.getLogger("destinepyauth").setLevel(log_level)

    # Load configuration for the service
    config, scope, hook = ConfigurationFactory.load_config(service)

    # Create and run authentication
    auth_service = AuthenticationService(
        config=config,
        scope=scope,
        post_auth_hook=hook,
    )

    result = auth_service.login(write_netrc=write_netrc, twofa=twofa)

    if not write_netrc:
        return result
