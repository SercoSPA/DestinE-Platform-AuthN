"""Service registry and configuration factory."""

from pathlib import Path

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
    def load_config(service_name: str) -> BaseConfig:
        """
        Load configuration for a service.

        Loads the service's default configuration from YAML using Conflator,
        which automatically merges with user overrides from environment variables,
        CLI args, and user config files.

        Args:
            service_name: Name of the service to configure.

        Returns:
            BaseConfig with all service-specific settings including scope and exchange_config.

        Raises:
            ValueError: If the service is unknown.
        """
        # Get the service config file path
        config_path = ServiceRegistry.get_service_config_path(service_name)

        # Load config using Conflator with the service YAML as the config file
        # Conflator will merge: service YAML → user config files → env vars → CLI args
        config = Conflator("despauth", BaseConfig, config_file=config_path).load()

        return config
