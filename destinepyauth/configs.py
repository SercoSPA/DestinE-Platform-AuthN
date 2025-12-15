#! /usr/bin/env python3
"""Configuration model for DESP authentication."""

from typing import Annotated

from conflator import CLIArg, ConfigModel, EnvVar
from pydantic import Field


class BaseConfig(ConfigModel):
    """Base configuration for DESP authentication."""

    user: Annotated[
        str | None,
        Field(description="Your DESP username (via DESPAUTH_USER env var or prompt)"),
        EnvVar("USER"),
    ] = None

    password: Annotated[
        str | None,
        Field(description="Your DESP password (via DESPAUTH_PASSWORD env var or prompt)"),
        EnvVar("PASSWORD"),
    ] = None

    iam_url: Annotated[
        str,
        Field(description="The URL of the IAM server"),
        CLIArg("--iam-url"),
        EnvVar("IAM_URL"),
    ] = "https://auth.destine.eu"

    iam_realm: Annotated[
        str,
        Field(description="The realm of the IAM server"),
        CLIArg("--iam-realm"),
        EnvVar("REALM"),
    ] = "desp"

    iam_client: Annotated[
        str | None,
        Field(description="The client ID of the IAM server"),
        CLIArg("--iam-client"),
        EnvVar("CLIENT_ID"),
    ] = None

    iam_redirect_uri: Annotated[
        str | None,
        Field(description="Redirect URI"),
        CLIArg("--redirect-uri"),
        EnvVar("REDIRECT_URI"),
    ] = None
