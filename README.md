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
### Two Factor Authentication

If you have 2FA enabled, you will be prompted to enter an OTP from your authenticator app.

You can enable/disable 2FA in your [DestinE platform account settings](https://auth.destine.eu/realms/desp/account/).

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
- `highway` - Highway service (includes token exchange)
- `insula` - Insula service
- `streamer` - Streaming service

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

## Adding a new service

To integrate a new DestinE service, add an entry to the `_REGISTRY` dictionary in the [ServiceRegistry class](./destinepyauth/services.py):

```python
"your_service": {
    "scope": "openid offline_access",  # OAuth scopes required
    "defaults": {
        "iam_client": "your-client-id",  # From service's IAM registration
        "iam_redirect_uri": "https://your-service.destine.eu/",  # OAuth redirect
    },
    # Optional: only if post-authentication processing is needed
    # "post_auth_hook": your_custom_hook_function,
},
```
