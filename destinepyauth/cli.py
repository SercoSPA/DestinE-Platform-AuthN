#!/usr/bin/env python3
"""Command-line interface for DESP authentication."""

import sys
import argparse
import logging

from destinepyauth.services import ServiceRegistry
from destinepyauth.exceptions import AuthenticationError
from destinepyauth.get_token import get_token


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
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
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

    try:
        result = get_token(args.SERVICE, write_netrc=args.netrc, verbose=args.verbose)
        # Output the token
        if args.print:
            print(result.access_token)

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
