import time
from collections.abc import Callable

from server_runner.config.logging import get_logger
from server_runner.steam.api.rest_api_base import RESTSteamServerAPI
from server_runner.steam.server.controller import SteamServerController

log = get_logger()


class GameServerManager:
    """
    High-level interface for managing a game server instance,
    including process lifecycle and API interactions.
    """

    def __init__(self, controller: SteamServerController, api: RESTSteamServerAPI):
        self.controller = controller
        self.api = api

    # ---------- Lifecycle Management ----------

    def start(self) -> None:
        """Start the game server."""
        log.debug("Starting server...")
        self.controller.start()

    def stop(self) -> None:
        """Stop the game server gracefully."""
        log.debug("Stopping server...")
        self.api.stop()
        self.controller.stop()

    def restart(self, auto_update: bool = True) -> None:
        """Restart the game server, optionally auto-updating before restart."""
        log.debug(f"Restarting server (auto_update={auto_update})...")
        self.controller.restart(auto_update=auto_update)

    def is_running(self) -> bool:
        """Return True if the server process is running."""
        return self.controller.is_running()

    def is_update_available(self) -> bool:
        """Return True if the server process is running."""
        return self.controller.is_update_available()

    def force_stop(self) -> None:
        """Force stop the server immediately."""
        log.debug("Force stopping server...")
        self.controller.stop()

    # ---------- API Actions ----------

    def announce(self, message: str) -> None:
        """Send an announcement via the game API."""
        self.api.announce(message)

    def save(self) -> None:
        """Trigger a server save."""
        self.api.save()

    def shutdown(self, message: str, delay: int) -> None:
        """Shutdown the server with a message and delay."""
        self.api.shutdown(message, delay)

    # ---------- Utilities ----------

    def wait(self, seconds: float) -> None:
        """Sleep for a number of seconds."""
        time.sleep(seconds)

    def wait_for(
        self, condition: Callable[[], bool], timeout: int = 15, interval: float = 1.0
    ) -> bool:
        """
        Wait for a condition to become True.

        Args:
            condition: Callable returning a boolean.
            timeout: Maximum time to wait in seconds.
            interval: How often to check the condition.

        Returns:
            True if condition became True within timeout, False otherwise.
        """
        start = time.time()
        while time.time() - start < timeout:
            if condition():
                return True
            self.wait(interval)
        return False
