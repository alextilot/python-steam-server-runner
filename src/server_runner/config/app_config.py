import os
from dataclasses import dataclass, field

from dotenv import load_dotenv  # type: ignore[reportUnknownMemberType]

from server_runner.config.logging import get_logger

log = get_logger()

load_dotenv()


@dataclass
class AppConfig:
    app_environment: str
    is_production: bool = field(init=False)
    debug_mode: bool = False  # Default value

    def __post_init__(self):
        # Determine is_production based on app_environment
        self.is_production = self.app_environment == "production"

    @classmethod
    def from_env(cls):
        # Helper function to get required env vars or raise an error
        def get_required_env(key: str) -> str:
            value = os.getenv(key)
            if value is None:
                raise ValueError(f"Required environment variable '{key}' not set.")
            return value

        return cls(
            app_environment=get_required_env("APP_ENV").lower(),
            # 'False' is the default if DEBUG_MODE is missing
            debug_mode=os.getenv("DEBUG_MODE", "False").lower() == "true",
        )


try:
    app_config = AppConfig.from_env()
except ValueError as e:
    log.error("Configuration Error: %s", e)
    # Exit the application cleanly if configuration fails
    exit(1)
