#!/usr/bin/env python3
"""Command-line interface for DESP authentication."""

import sys
import argparse
import logging
from pathlib import Path

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
        "--service",
        "-s",
        required=False,
        type=str,
        help="Service name to authenticate against (optional with --config)",
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to custom YAML service config (optional)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    # Create mutually exclusive group for output options
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--netrc",
        "-n",
        action="store_true",
        help="Write/update token in ~/.netrc file for the service host",
    )
    output_group.add_argument(
        "--print",
        "-p",
        action="store_true",
        help="Print the token output",
    )

    args = parser.parse_args()

    if not args.service and not args.config:
        parser.error("Either --service/-s or --config/-c must be provided")

    if args.service and not args.config and args.service not in ServiceRegistry.list_services():
        parser.error(
            f"Unknown service '{args.service}'. Available: {', '.join(ServiceRegistry.list_services())}"
        )

    service_name = args.service
    if service_name is None:
        # Derive a stable service label from the custom config filename.
        service_name = Path(args.config).stem

    try:
        result = get_token(
            service=service_name,
            config_path=args.config,
            write_netrc=args.netrc,
            verbose=args.verbose,
        )
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
