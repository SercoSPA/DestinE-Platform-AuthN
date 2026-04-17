![DestinE Banner](assets/DestinE-banner.jpg)

# destinepyauth

[![Tests](https://img.shields.io/github/actions/workflow/status/SercoSPA/DestinE-Platform-AuthN/ci.yml?branch=main&label=tests)](https://github.com/SercoSPA/DestinE-Platform-AuthN/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/SercoSPA/DestinE-Platform-AuthN?label=coverage)](https://codecov.io/gh/SercoSPA/DestinE-Platform-AuthN)
[![PyPI](https://img.shields.io/pypi/v/destinepyauth)](https://pypi.org/project/destinepyauth/)
[![Python Versions](https://img.shields.io/pypi/pyversions/destinepyauth)](https://pypi.org/project/destinepyauth/)
[![License](https://img.shields.io/pypi/l/destinepyauth)](https://github.com/SercoSPA/DestinE-Platform-AuthN/blob/main/LICENSE)

A Python library for authenticating against DESP (Destination Earth Service Platform) services.

## Installation

```bash
pip install destinepyauth
```

## Usage

The main entry point is the `get_token()` function.

For example, obtain an access token for the `highway` service:
```python
from destinepyauth import get_token

# Authenticate (prompts for credentials if not in environment)
result = get_token("highway")

# Access the tokens
access_token = result.access_token
refresh_token = result.refresh_token
```

### Available Services

- `cacheb` - CacheB data service
- `dea` - DEA service
- `eden` - EDEN broker
- `hda` - Harmonized Data Access
- `highway` - Highway service
- `insula` - Insula service
- `polytope` - Data access service
- `streamer` - DestinEStreamer

Please see [below instructions for using a custom service](#custom-services).

### Using with requests

```python
from destinepyauth import get_token
import requests

result = get_token("eden")
headers = {"Authorization": f"Bearer {result.access_token}"}
response = requests.get("https://api.example.com/data", headers=headers)
```

### Using with zarr/xarray (netrc support)

For services like CacheB that work with zarr, you can write a refresh token to `~/.netrc`:

```python
from destinepyauth import get_token
import xarray as xr

# Authenticate and write to ~/.netrc
get_token("cacheb", write_netrc=True)

# Now zarr/xarray will use credentials automatically
ds = xr.open_dataset(
    "reference://",
    engine="zarr",
    backend_kwargs={
        "consolidated": False,
        "storage_options": {
            "fo": "https://cacheb.dcms.destine.eu/path/to/data.json",
            "remote_protocol": "https",
            "remote_options": {"client_kwargs": {"trust_env": True}},
        },
    },
)
```

### Polytope compatibility (`~/.polytopeapirc`)

When authenticating with `get_token("polytope")`, the library automatically writes the
refresh token to `~/.polytopeapirc` as JSON (`{"user_key": "..."}`), matching the
expected Polytope client format.

### Custom services

You can authenticate against a custom service by passing
the path to a YAML config file:

```python
from destinepyauth import get_token

result = get_token(config_path="/path/to/myservice.yaml")
token = result.access_token
```

where the config file should be in the following format:
```yaml
# Example: myservice.yaml
scope: openid offline_access
iam_client: myservice-public
iam_redirect_uri: https://myservice.destine.eu/

# Optional: Token exchange configuration (only if needed)
exchange_config:
  token_url: https://identity.example.com/token
  audience: myservice-public
  subject_issuer: desp-oidc
  client_id: myservice-public
```

#### Service Configuration Fields

- **`scope`**: OAuth2 scopes (e.g., `"openid"`, `"openid offline_access"`)
- **`iam_client`**: Client ID registered with the IAM (Identity and Access Management)
- **`iam_redirect_uri`**: OAuth redirect URI for the service
- **`iam_url`** (optional): IAM server URL (defaults to `https://auth.destine.eu`)
- **`iam_realm`** (optional): IAM realm (defaults to `desp`)

Some services (like Highway and HDA) require token exchange because they validate tokens against a different issuer than the initial login. For these services, an `exchange_config` section is necessary:

- **`token_url`**: Token exchange endpoint
- **`audience`**: Target audience for the exchanged token
- **`subject_issuer`**: Subject issuer identifier
- **`client_id`**: Client ID for the exchange request

The library automatically handles token exchange using [RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693) when `exchange_config` is present.

### CLI Usage

```bash
# Built-in service
destinepyauth -s highway --print

# Custom service config file
destinepyauth -c path/to/myservice.yaml --print
```

## Credential Handling

When you call `get_token()`, the library will prompt for your credentials. The password
uses **masked input** - nothing you type will be visible on screen:

```python
from destinepyauth import get_token
result = get_token("highway")
# Username: myuser
# Password:   (hidden input)
```

This ensures the password cannot be accidentally exposed in terminal logs, screen recordings,
or shell history.

You can also provide credentials via environment variables to avoid interactive prompts:

```bash
export DESPAUTH_USER='<your-username>'
export DESPAUTH_PASSWORD='<your-password>'
```

When `DESPAUTH_USER` and `DESPAUTH_PASSWORD` are set, `get_token()` uses them directly.

### Two Factor Authentication

If you have 2FA enabled, you will also be prompted to enter an OTP from your authenticator app.

You can enable/disable 2FA in your [DESP account settings](https://auth.destine.eu/realms/desp/account/).

## Configuration

Service configurations are stored in YAML files in the `destinepyauth/configs/` directory. Each service has its own configuration file (e.g., `highway.yaml`, `cacheb.yaml`) that defines default values for authentication parameters.

### Configuration Priority

The library uses [Conflator](https://github.com/ecmwf/conflator) to merge configuration values.

The base configuration file is:

- Built-in service YAML (`destinepyauth/configs/{service}.yaml`) when using `get_token("service")` or `destinepyauth -s service`
- Your custom YAML when using `get_token(config_path=...)` or `destinepyauth -c ...`

Environment variables (`DESPAUTH_*`) override values from that base config file.

If both a service and a custom config path are provided (for example, `destinepyauth -s hda -c config.yaml`),
the custom config file is used as the base configuration.

## Adding a new service

To integrate a new DestinE service, either:
* Fork the repository, add a new configuration file to `destinepyauth/configs/{service_name}.yaml`, and then open a pull request
* OR open an issue with a request to integrate a new service

