"""High-level API for DESP authentication."""

import logging
from pathlib import Path
from typing import Optional

from destinepyauth.authentication import AuthenticationService, TokenResult
from destinepyauth.services import ConfigurationFactory


def get_token(
    service: Optional[str] = None,
    config_path: Optional[str] = None,
    write_netrc: bool = False,
    verbose: bool = False,
) -> Optional[TokenResult]:
    """
    Authenticate and get an access token for a DESP service.

    Credentials are obtained securely via:
    - Environment variables (DESPAUTH_USER, DESPAUTH_PASSWORD)
    - Interactive prompt with masked password input
    If DESPAUTH_USER and DESPAUTH_PASSWORD are set, no interactive credential
    prompt is shown.

    Args:
        service: Service name (e.g., 'highway', 'cacheb', 'eden'). Optional when
            config_path is provided.
        config_path: Optional path to a custom YAML config file. When provided,
            this config is used instead of built-in service defaults.
        write_netrc: If True, write/update the token in ~/.netrc file.
        verbose: If True, enable DEBUG logging.

    Returns:
        TokenResult containing the access token and decoded payload.
        Returns None if write_netrc=True to prevent token exposure in output.

    Raises:
        AuthenticationError: If authentication fails.
        ValueError: If neither service nor config_path are provided, if service
            name is not recognized (without config_path), or if config_path is invalid.
    """
    if service is None and config_path is None:
        raise ValueError("Either service or config_path must be provided")

    service_name = service
    if service_name is None and config_path is not None:
        service_name = Path(config_path).stem

    # Configure only the library logger (do not change the root logger).
    # Applications (including notebooks) should configure handlers.
    log_level = logging.INFO if not verbose else logging.DEBUG
    logging.getLogger("destinepyauth").setLevel(log_level)

    # Load configuration for the service
    config = ConfigurationFactory.load_config(service_name, config_path=config_path)

    # Create and run authentication
    auth_service = AuthenticationService(config=config, service_name=service_name)

    result = auth_service.login(write_netrc=write_netrc)

    if not write_netrc:
        return result
