# destinepyauth

A Python library for authenticating against DESP (Destination Earth Service Platform) services.

## Installation

```bash
pip install destinepyauth
```

## Usage

The main entry point is the `get_token()` function:

```python
from destinepyauth import get_token

# Authenticate (prompts for credentials if not in environment)
result = get_token("highway")

# Access the token
token = result.access_token
```

### Using with requests

```python
from destinepyauth import get_token
import requests

result = get_token("eden")
headers = {"Authorization": f"Bearer {result.access_token}"}
response = requests.get("https://api.example.com/data", headers=headers)
```

### Using with zarr/xarray (netrc support)

For services like CacheB that work with zarr, you can write credentials to `~/.netrc`:

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

## Available Services

- `cacheb` - CacheB data service
- `dea` - DEA service
- `eden` - Eden broker
- `hda` - Harmonized Data Access (includes token exchange)
- `highway` - Highway service (includes token exchange)
- `insula` - Insula service
- `streamer` - Streaming service

## Configuration

Service configurations are stored in YAML files in the `destinepyauth/configs/` directory. Each service has its own configuration file (e.g., `highway.yaml`, `cacheb.yaml`) that defines default values for authentication parameters.

### Configuration Priority

The library uses [Conflator](https://github.com/ecmwf/conflator) to merge configurations from multiple sources, with the following priority (highest to lowest):

1. **Command-line arguments** (e.g., `--iam-client my-client`)
2. **Environment variables** (e.g., `DESPAUTH_IAM_CLIENT=my-client`)
3. **User config files** (e.g., `~/.despauth.yaml`)
4. **Service defaults** (from `destinepyauth/configs/{service}.yaml`)

This allows you to override any service default without modifying the package.

### Example: Override IAM Client

```bash
# Via environment variable
export DESPAUTH_IAM_CLIENT=my-custom-client
python -c "from destinepyauth import get_token; get_token('highway')"

# Via user config file
echo "iam_client: my-custom-client" > ~/.despauth.yaml
python -c "from destinepyauth import get_token; get_token('highway')"
```

## Credential Handling

When you call `get_token()`, the library will prompt for your credentials with **masked input**
for both username and password - nothing you type will be visible on screen:

```python
from destinepyauth import get_token
result = get_token("highway")
# Username:   (hidden input)
# Password:   (hidden input)
```

This ensures credentials cannot be accidentally exposed in terminal logs, screen recordings,
or shell history.

### Two Factor Authentication

If you have 2FA enabled, you will also be prompted to enter an OTP from your authenticator app.

You can enable/disable 2FA in your [DestinE platform account settings](https://auth.destine.eu/realms/desp/account/).

## Adding a new service

To integrate a new DestinE service, create a YAML configuration file in `destinepyauth/configs/{service_name}.yaml`:

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

The service will be automatically discovered and available via `get_token("myservice")`.

### Service Configuration Fields

- **`scope`**: OAuth2 scopes (e.g., `"openid"`, `"openid offline_access"`)
- **`iam_client`**: Client ID registered with the IAM
- **`iam_redirect_uri`**: OAuth redirect URI for the service
- **`iam_url`** (optional): IAM server URL (defaults to `https://auth.destine.eu`)
- **`iam_realm`** (optional): IAM realm (defaults to `desp`)

### Token Exchange

Some services (like Highway and HDA) require token exchange because they validate tokens against a different issuer than the initial login. For these services, add an `exchange_config` section:

- **`token_url`**: Token exchange endpoint
- **`audience`**: Target audience for the exchanged token
- **`subject_issuer`**: Subject issuer identifier
- **`client_id`**: Client ID for the exchange request

The library automatically handles token exchange using [RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693) when `exchange_config` is present.
