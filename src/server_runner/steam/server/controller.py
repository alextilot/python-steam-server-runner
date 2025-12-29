import logging
import os.path

from steam_version_manager import SteamVersionManager
from utils.managed_process import ManagedProcess
from validators.os import os_path_exists_raise

log = logging.getLogger(__name__)


class SteamGameController:
    """
    Manages a single Steam game instance:
      - Starts, stops, and restarts the game process
      - Provides access to version management
      - Optionally integrates auto-update behavior
    """

    STEAM_APPS_DIR = "steamapps/common"

    def __init__(
        self,
        steam_path: str,
        app_id: str | int,
        game_name: str,
        server_arguments: list[str] | None = None,
    ):
        os_path_exists_raise(steam_path)

        self.steam_path = steam_path
        self.app_id = str(app_id)
        self.game_name = game_name
        self.server_arguments = server_arguments or []

        # Path to the game's shell script
        game_shell_script = os.path.join(
            steam_path, self.STEAM_APPS_DIR, game_name, f"{game_name}.sh"
        )

        # Command as a list for safe execution
        self.game_command = [game_shell_script] + self.server_arguments

        self.managed_process: ManagedProcess | None = None
        self.version_manager = SteamVersionManager(app_id)

    # ---------- process management ----------
    def start(self, auto_update: bool = False) -> None:
        """Start the game. Optionally auto-update before starting."""
        if self.is_running():
            log.warning(f"{self.game_name} already running (PID {self.pid()})")
            return

        if auto_update and self.version_manager.is_update_available():
            log.info(f"Auto-update enabled, updating {self.game_name}...")
            self.version_manager.update()

        self.managed_process = ManagedProcess(self.game_command, shell=False)
        self.managed_process.start()
        log.info(f"Started {self.game_name} (PID {self.pid()})")

    def stop(self) -> None:
        """Stop the game process if running."""
        if self.managed_process:
            self.managed_process.terminate(timeout=10)
            log.info(f"Stopped {self.game_name}")
            self.managed_process = None

    def restart(self, auto_update: bool = False) -> None:
        """Restart the game process. Optionally auto-update before restart."""
        if self.managed_process:
            self.stop()
        self.start(auto_update=auto_update)

    def is_running(self) -> bool:
        """Return True if the game process is currently running."""
        return self.managed_process.is_running() if self.managed_process else False

    def pid(self) -> int | None:
        """Return the PID of the game process if running."""
        return self.managed_process.pid() if self.managed_process else None

    def is_update_available(self) -> bool:
        """
        Check if a new update is available for this game.

        Returns:
            True if the latest Steam build is newer than the current one.
        """
        try:
            return self.version_manager.is_update_available()
        except Exception as e:
            log.error(f"Failed to check for updates: {e}")
            return False
