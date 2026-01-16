"""Service registry and configuration factory."""

from typing import Dict, Any, Tuple, Callable, Optional

from conflator import Conflator

from destinepyauth.configs import BaseConfig
from destinepyauth.hooks import token_exchange


class ServiceRegistry:
    """Registry mapping service names to their configuration."""

    _REGISTRY: Dict[str, Dict[str, Any]] = {
        "cacheb": {
            "scope": "openid offline_access",
            "defaults": {
                "iam_client": "edh-public",
                "iam_redirect_uri": "https://cacheb.dcms.destine.eu/",
            },
        },
        "streamer": {
            "scope": "openid",
            "defaults": {
                "iam_client": "streaming-fe",
                "iam_redirect_uri": "https://streamer.destine.eu/",
            },
        },
        "insula": {
            "scope": "openid",
            "defaults": {
                "iam_client": "insula-public",
                "iam_redirect_uri": "https://insula.destine.eu/",
            },
        },
        "eden": {
            "scope": "openid",
            "defaults": {
                "iam_client": "hda-broker-public",
                "iam_redirect_uri": "https://broker.eden.destine.eu/",
            },
        },
        "dea": {
            "scope": "openid",
            "defaults": {
                "iam_client": "dea_client",
                "iam_redirect_uri": "https://dea.destine.eu/",
            },
        },
        "highway": {
            "scope": "openid",
            "defaults": {
                "iam_client": "highway-public",
                "iam_redirect_uri": "https://highway.esa.int/sso/auth/realms/highway/broker/DESP_IAM_PROD/endpoint",
            },
            "token_exchange": {
                "token_url": "https://highway.esa.int/sso/auth/realms/highway/protocol/openid-connect/token",
                "audience": "highway-public",
                "subject_issuer": "DESP_IAM_PROD",
                "client_id": "highway-public",
            },
        },
        "polytope": {
            "scope": "openid offline_access",
            "defaults": {
                "iam_client": "polytope-api-public",
                "iam_redirect_uri": "https://polytope.lumi.apps.dte.destination-earth.eu/",
            },
        },
        "hda": {
            "scope": "openid",
            "defaults": {
                "iam_client": "dedl-hda",
                "iam_redirect_uri": "https://hda.data.destination-earth.eu/stac",
            },
            "token_exchange": {
                "token_url": "https://identity.data.destination-earth.eu/auth/realms/dedl/protocol/openid-connect/token",
                "audience": "hda-public",
                "subject_issuer": "desp-oidc",
                "client_id": "hda-public",
            },
        },
    }

    @classmethod
    def get_service_info(cls, service_name: str) -> Dict[str, Any]:
        """
        Get configuration info for a service.

        Args:
            service_name: Name of the service (e.g., 'eden', 'highway').

        Returns:
            Dictionary containing scope, defaults, and optional hooks.

        Raises:
            ValueError: If the service name is not registered.
        """
        if service_name not in cls._REGISTRY:
            available = ", ".join(cls._REGISTRY.keys())
            raise ValueError(f"Unknown service: {service_name}. Available: {available}")
        return cls._REGISTRY[service_name]

    @classmethod
    def list_services(cls) -> list[str]:
        """
        List all available service names.

        Returns:
            List of registered service names.
        """
        return list(cls._REGISTRY.keys())


class ConfigurationFactory:
    """Factory for loading service configurations using Conflator."""

    @staticmethod
    def load_config(service_name: str) -> Tuple[BaseConfig, str, Optional[Callable[[str, BaseConfig], str]]]:
        """
        Load configuration for a service.

        Args:
            service_name: Name of the service to configure.

        Returns:
            Tuple of (config, scope, post_auth_hook).
        """
        service_info = ServiceRegistry.get_service_info(service_name)
        scope: str = service_info["scope"]
        defaults: Dict[str, Any] = service_info.get("defaults", {})
        exchange_cfg: Optional[Dict[str, Any]] = service_info.get("token_exchange")

        # Load configuration using Conflator
        config: BaseConfig = Conflator("despauth", BaseConfig).load()

        # Apply service defaults for any values not explicitly set
        for key, default_value in defaults.items():
            current_value = getattr(config, key, None)
            if current_value is None:
                setattr(config, key, default_value)

        # If no explicit hook is provided, optionally build a token-exchange hook from registry config.
        if exchange_cfg is not None:
            token_url = exchange_cfg["token_url"]
            audience = exchange_cfg["audience"]
            subject_issuer = exchange_cfg["subject_issuer"]
            client_id = exchange_cfg.get("client_id")

            def _exchange_hook(access_token: str, cfg: BaseConfig) -> str:
                return token_exchange(
                    token_url=token_url,
                    subject_token=access_token,
                    client_id=client_id,
                    audience=audience,
                    subject_issuer=subject_issuer,
                    timeout=10,
                )

            hook = _exchange_hook

        return config, scope, hook
