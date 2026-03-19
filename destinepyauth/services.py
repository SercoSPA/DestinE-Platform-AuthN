"""Service registry and configuration factory."""

from pathlib import Path
from typing import Optional

from conflator import Conflator

from destinepyauth.configs import BaseConfig


class ServiceRegistry:
    """Registry mapping service names to their configuration."""

    @classmethod
    def _get_configs_dir(cls) -> Path:
        """Get the path to the configs directory."""
        return Path(__file__).parent / "configs"

    @classmethod
    def list_services(cls) -> list[str]:
        """
        List all available service names.

        Returns:
            List of registered service names (based on available YAML files).
        """
        configs_dir = cls._get_configs_dir()
        if not configs_dir.exists():
            return []
        return [f.stem for f in configs_dir.glob("*.yaml")]

    @classmethod
    def service_config_exists(cls, service_name: str) -> bool:
        """
        Check if a service configuration file exists.

        Args:
            service_name: Name of the service.

        Returns:
            True if the service config file exists.
        """
        config_file = cls._get_configs_dir() / f"{service_name}.yaml"
        return config_file.exists()

    @classmethod
    def get_service_config_path(cls, service_name: str) -> Path:
        """
        Get the path to a service configuration file.

        Args:
            service_name: Name of the service.

        Returns:
            Path to the service configuration file.

        Raises:
            ValueError: If the service configuration file doesn't exist.
        """
        if not cls.service_config_exists(service_name):
            available = ", ".join(cls.list_services())
            raise ValueError(f"Unknown service: {service_name}. Available: {available}")
        return cls._get_configs_dir() / f"{service_name}.yaml"


class ConfigurationFactory:
    """Factory for loading service configurations using Conflator."""

    @staticmethod
    def load_config(service_name: str, config_path: Optional[str] = None) -> BaseConfig:
        """
        Load configuration for a service.

        Loads configuration from either a built-in service YAML file or an explicit
        custom YAML file path, then applies environment/CLI overrides handled by
        Conflator.

        Args:
            service_name: Name of the service to configure.
            config_path: Optional path to a custom service YAML config.
                If provided, this config is used instead of built-in service defaults.

        Returns:
            BaseConfig with all service-specific settings including scope and exchange_config.

        Raises:
            ValueError: If the service is unknown (when config_path is not provided)
                or if config_path does not exist.
        """
        if config_path is not None:
            resolved_config_path = Path(config_path).expanduser().resolve()
            if not resolved_config_path.exists():
                raise ValueError(f"Config file does not exist: {resolved_config_path}")
        else:
            resolved_config_path = ServiceRegistry.get_service_config_path(service_name)

        # Load config using Conflator with the service YAML as the config file
        # Conflator uses the selected YAML file as base config and then applies
        # environment/CLI overrides.
        config = Conflator("despauth", BaseConfig, config_file=resolved_config_path).load()

        return config
