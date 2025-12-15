"""Service registry and configuration factory."""

from typing import Dict, Any, Tuple, Callable, Optional

from conflator import Conflator

from destinepyauth.configs import BaseConfig
from destinepyauth.hooks import highway_token_exchange


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
                # Highway uses a special redirect URI for DESP broker
                "iam_redirect_uri": "https://highway.esa.int/sso/auth/realms/highway/broker/DESP_IAM_PROD/endpoint",
            },
            "post_auth_hook": highway_token_exchange,
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
        hook: Optional[Callable[[str, BaseConfig], str]] = service_info.get("post_auth_hook")

        # Load configuration using Conflator
        config: BaseConfig = Conflator("despauth", BaseConfig).load()

        # Apply service defaults for any values not explicitly set
        for key, default_value in defaults.items():
            current_value = getattr(config, key, None)
            if current_value is None:
                setattr(config, key, default_value)

        return config, scope, hook
