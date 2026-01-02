#!/usr/bin/env python3
"""Command-line interface for DESP authentication."""

import sys
import argparse
import json
import logging
from typing import Dict, Any

from destinepyauth.services import ConfigurationFactory, ServiceRegistry
from destinepyauth.authentication import AuthenticationService, TokenResult
from destinepyauth.exceptions import AuthenticationError


def output_token(result: TokenResult, output_format: str) -> None:
    """
    Output the token in the specified format.

    Args:
        result: TokenResult from authentication.
        output_format: One of 'json', 'token'.
    """
    if output_format == "json":
        output: Dict[str, Any] = {
            "access_token": result.access_token,
            "token_type": "Bearer",
        }
        if result.decoded:
            output["decoded"] = result.decoded
        print(json.dumps(output, indent=2))
    elif output_format == "token":
        print(result.access_token)
    else:
        raise ValueError(f"Unknown output format: {output_format}")


def main() -> None:
    """
    Main entry point for the authentication CLI.

    Parses command-line arguments, loads service configuration,
    and executes the authentication flow.
    """
    parser = argparse.ArgumentParser(
        description="Get authentication token from DESP IAM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Available services: {', '.join(ServiceRegistry.list_services())}",
    )

    parser.add_argument(
        "--SERVICE",
        "-s",
        required=True,
        type=str,
        choices=ServiceRegistry.list_services(),
        help="Service name to authenticate against",
    )

    parser.add_argument(
        "--twofa",
        action="store_true",
        help="Use explicit 2FA (OTP) login flow",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        choices=["json", "token"],
        default="token",
        help="Output format: 'json' (full JSON), 'token' (just token)",
    )

    parser.add_argument(
        "--netrc",
        "-n",
        action="store_true",
        help="Write/update token in ~/.netrc file for the service host",
    )

    parser.add_argument(
        "--print",
        "-p",
        action="store_true",
        help="Print the token output",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    try:
        # Load configuration
        config, scope, hook = ConfigurationFactory.load_config(args.SERVICE)

        # Initialize and execute authentication
        auth_service = AuthenticationService(
            config=config,
            scope=scope,
            post_auth_hook=hook,
        )
        if args.twofa:
            result = auth_service.login_2fa(write_netrc=args.netrc)
        else:
            result = auth_service.login(write_netrc=args.netrc)

        # Output the token
        if args.print:
            output_token(result, args.output)

    except AuthenticationError as e:
        logging.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logging.error("Authentication cancelled")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
