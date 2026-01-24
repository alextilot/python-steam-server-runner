from enum import Enum, auto

from server_runner.config.logging import get_logger
from server_runner.steam.api.rest_api_base import RESTSteamServerAPI
from server_runner.steam.server.controller import SteamServerController
from server_runner.utils.wait import Wait

log = get_logger()


class StopMode(Enum):
    GRACEFUL = auto()
    FORCE = auto()


class ServerState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    STOPPING = auto()
    UNKNOWN = auto()


class GameServerManager:
    ServerState = ServerState
    StopMode = StopMode
    """
    High-level interface for managing a game server instance,
    including process lifecycle and API interactions.
    """

    def __init__(
        self, controller: SteamServerController, api: RESTSteamServerAPI, wait: Wait
    ):
        self.controller = controller
        self.api = api
        self.wait = wait

    def is_out_of_memory(self) -> bool:
        return self.controller.get_memory_usage() >= 80.0

    def start(self) -> None:
        """Start the game server."""
        if self.controller.is_running():
            log.warning("Server already running")
            return
        self.controller.start()

    def stop(self, mode: StopMode = StopMode.GRACEFUL, timeout: int = 60) -> None:
        """Stop the game server, waiting for it to stop, optionally forcing if needed."""
        if not self.controller.is_running():
            log.info("Server already stopped")
            return

        if mode is StopMode.FORCE:
            log.info("Force stop requested")
            self.controller.stop()
            return

        # Graceful shutdown
        log.debug("Saving server state before graceful shutdown")
        self.api.save()

        log.info("Requesting graceful shutdown via API")
        self.api.shutdown("Server shutting down", delay=5)

        stopped = self.wait.until(
            lambda: not self.controller.is_running(), timeout=timeout
        )
        if stopped:
            log.info("Server stopped successfully")
            return

        # Graceful failed → force stop
        log.warning("Server did not stop in time, forcing stop")
        self.controller.stop()
        self.wait.until(lambda: not self.controller.is_running(), timeout=30)
        log.info("Server force-stopped")

    def update(self) -> None:
        """
        Update the server if an update is available.

        Safe to call at any time. If the server is running, it will be
        stopped before applying the update.
        """
        if not self.controller.is_update_available():
            log.debug("No server update available")
            return

        log.info("Server update available")

        self.stop(StopMode.GRACEFUL)

        log.info("Applying server update")
        self.controller.update()

    def update_available(self) -> bool:
        return self.controller.is_update_available()

    def state(self) -> ServerState:
        if self.controller.is_running():
            return ServerState.RUNNING

        # Future extension: ping API health
        return ServerState.STOPPED

    def announce(self, message: str) -> bool:
        if not self.controller.is_running():
            log.debug("Skipping announce; server not running")
            return False
        self.api.announce(message)
        return True
