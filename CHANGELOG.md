# Changelog

All notable changes to this project will be documented in this file.

This changelog should be updated with every pull request with some information about what has been changed. These changes can be added under a temporary title 'pre-release'.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Each release can have sections: "Added", "Changed", "Deprecated", "Removed", "Fixed" and "Security".

## [1.1.0] - 20-01-2026

## added

- authentication for data lake HDA
- authentication for Polytope

## changed

- renamed api.py to get_token.py
- renamed auth.py to cli.py
- refactored service configuration system to use YAML files instead of Python dictionaries
- service configurations now stored in `destinepyauth/configs/` directory
- improved configuration priority: CLI args → env vars → user config files → service defaults

## fix

- add small leeway (30s) for token verification to avoid errors about token being issued in the future

## [1.0.0] - 05-01-2026

## added

- 2FA support: users will be prompted to enter OTP if 2FA is enabled
- instructions for adding a new service

## [0.2.3] - 12-12-2025

# security

- avoid accidentally printing token when write_netrc=True or using CLI

## [0.2.2] - 11-12-2025

# added

- automatic version update and github release with git tagging

## [0.2.1] - 10-12-2025

# added

- CD to publish to PyPI

# changed

- changed repository visibility to public
- remove unnecessary dependencies and classifiers from pyproject.toml

## [0.2.0] - 10-12-2025

## added

- test authentication in CI

## security

- prompt for credentials ONLY
- dependabot to check vulenrabilities
- detect secrets in pre-commit

## removed

- API parameters username, password

## [0.1.0] - 10-12-2025

### added

- Generate access tokens for DESP using CLI or the function "get_tokens"
- Github actions workflow to install, check linter errors, run tests on pull request
