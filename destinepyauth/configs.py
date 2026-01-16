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

    scope: Annotated[
        str,
        Field(description="OAuth2 scope"),
        CLIArg("--scope"),
        EnvVar("SCOPE"),
    ] = "openid"

    exchange_config: Annotated[
        "BaseExchangeConfig | None",
        Field(description="Token exchange configuration"),
    ] = None


class BaseExchangeConfig(ConfigModel):
    """Configuration for token exchange operations."""

    token_url: Annotated[
        str | None,
        Field(description="The token endpoint URL for exchange"),
        CLIArg("--token-url"),
        EnvVar("TOKEN_URL"),
    ] = None

    audience: Annotated[
        str | None,
        Field(description="The target audience for the exchanged token"),
        CLIArg("--audience"),
        EnvVar("AUDIENCE"),
    ] = None

    subject_issuer: Annotated[
        str | None,
        Field(description="The subject issuer for token exchange"),
        CLIArg("--subject-issuer"),
        EnvVar("SUBJECT_ISSUER"),
    ] = None

    client_id: Annotated[
        str | None,
        Field(description="The client ID for token exchange"),
        CLIArg("--client-id"),
        EnvVar("CLIENT_ID"),
    ] = None
