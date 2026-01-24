from enum import Enum, auto

from server_runner.config.logging import get_logger
from server_runner.steam.api.games.base_rest_api import RESTSteamServerAPI
from server_runner.steam.server.process import SteamServerProcess
from server_runner.utils.wait import Wait

log = get_logger()


class StopMode(Enum):
    GRACEFUL = auto()
    FORCE = auto()


class ServerState(Enum):
    RUNNING = auto()  # Process running and API responsive
    UNRESPONSIVE = auto()  # Process running, API not responding
    STOPPED = auto()  # Process is not running
    UNKNOWN = auto()  # Cannot determine state


class ManagedGameServer:
    """
    High-level interface for managing a game server instance,
    including process lifecycle and API interactions.
    """

    def __init__(
        self, process: SteamServerProcess, api: RESTSteamServerAPI, wait: Wait
    ):
        self.process = process
        self.api = api
        self.wait = wait

    # ---------------------------------------------------------------------
    # State
    # ---------------------------------------------------------------------

    def state(self) -> ServerState:
        process_alive = self.process.is_running()
        api_responsive = self.api.health_check()

        if not process_alive:
            return ServerState.STOPPED

        if not api_responsive:
            return ServerState.UNRESPONSIVE

        return ServerState.RUNNING

    def is_out_of_memory(self) -> bool:
        return self.process.get_memory_usage() >= 80.0

    # ---------------------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------------------

    def start(self) -> None:
        """Start the game server."""
        if self.process.is_running():
            log.warning("Server already running")
            return
        self.process.start()

    def stop(self, mode: StopMode = StopMode.GRACEFUL, timeout: int = 60) -> bool:
        """
        Stop the game server.

        GRACEFUL will attempt API shutdown first and escalate to FORCE
        if the server does not stop within the timeout.
        """
        state = self.state()

        if state is ServerState.STOPPED:
            log.info("Server already stopped")
            return True

        if mode is StopMode.FORCE:
            return self._stop_forcefully(timeout)

        if self._stop_gracefully(timeout):
            return True

        log.warning("Graceful shutdown failed; forcing stop")
        return self._stop_forcefully(timeout=30)

    def _stop_gracefully(
        self,
        timeout: int,
    ) -> bool:
        """Attempt a clean shutdown using the server API."""
        state = self.state()

        # Validate that it isn't already stopped
        if state is ServerState.STOPPED:
            return True

        # Validate that we can communicate via API
        if state is not ServerState.RUNNING:
            log.warning("Server not responsive; cannot stop gracefully")
            return False

        # Graceful shutdown
        log.debug("Saving server state before graceful shutdown")
        self.api.save()

        log.info("Requesting graceful shutdown via API")
        self.api.shutdown("Server shutting down", delay=5)

        stopped = self.wait.until(
            lambda: not self.process.is_running(),
            timeout=timeout,
        )

        if stopped:
            log.info("Server stopped successfully")
            return True

        return False

    def _stop_forcefully(self, timeout: int) -> bool:
        """Terminate the server process at the OS level."""
        state = self.state()

        # Validate that it isn't already stopped
        if state is ServerState.STOPPED:
            return True

        log.info("Force stopping server process")
        self.process.stop()

        stopped = self.wait.until(
            lambda: not self.process.is_running(),
            timeout=timeout,
        )

        if stopped:
            log.info("Server force-stopped successfully")
            return True

        log.error("Failed to force-stop server")
        return False

    # ---------------------------------------------------------------------
    # Operations
    # ---------------------------------------------------------------------

    def update_available(self) -> bool:
        return self.process.is_update_available()

    def update(self) -> None:
        """
        Update the server if an update is available.

        Safe to call at any time. If the server is running, it will be
        stopped before applying the update.
        """
        if not self.process.is_update_available():
            log.debug("No server update available")
            return

        log.info("Server update available")

        self.stop(StopMode.GRACEFUL)

        log.info("Applying server update")
        self.process.update()

    def announce(self, message: str) -> bool:
        if self.state() is not ServerState.RUNNING:
            log.debug("Skipping announce; server not running")
            return False

        self.api.announce(message)
        return True
