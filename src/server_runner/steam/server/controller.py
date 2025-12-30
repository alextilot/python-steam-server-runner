from server_runner.config.logging import get_logger
from server_runner.steam.server.manifest_helper import SteamManifestHelper
from server_runner.steam.server.version_manager import SteamServerVersionManager
from server_runner.utils.managed_process import ManagedProcess

log = get_logger()


class SteamServerController:
    """
    Manages a single Steam game instance (App ID driven):
      - Starts, stops, and restarts the game process
      - Provides access to version management
      - Optionally integrates auto-update behavior
    """

    def __init__(
        self,
        app_id: str | int,
        steam_path: str,
        server_arguments: list[str] | None = None,
    ):
        self.server_arguments = server_arguments or []

        # Use manifest helper to resolve the game directory
        self.manifest_helper = SteamManifestHelper(steam_path)
        self.game_dir = self.manifest_helper.get_game_dir(int(app_id))

        # Detect executable: assume same name as folder with .sh for Linux/macOS
        self.game_shell_script = self.game_dir / f"{self.game_dir.name}.sh"
        if not self.game_shell_script.exists():
            raise FileNotFoundError(
                f"Game executable not found: {self.game_shell_script}"
            )

        self.game_command = [str(self.game_shell_script)] + self.server_arguments
        self.managed_process: ManagedProcess | None = None
        self.version_manager = SteamServerVersionManager(app_id)

    # ---------- process management ----------
    def start(self, auto_update: bool = False) -> None:
        if self.is_running():
            log.warning(f"{self.game_dir.name} already running (PID {self.pid()})")
            return

        if auto_update and self.version_manager.is_update_available():
            log.info(f"Auto-update enabled, updating {self.game_dir.name}...")
            self.version_manager.update()

        self.managed_process = ManagedProcess(self.game_command, shell=True)
        self.managed_process.start()
        log.info(f"Started {self.game_dir.name} (PID {self.pid()})")

    def stop(self) -> None:
        if self.managed_process:
            self.managed_process.terminate(timeout=10)
            log.info(f"Stopped {self.game_dir.name}")
            self.managed_process = None

    def restart(self, auto_update: bool = False) -> None:
        if self.managed_process:
            self.stop()
        self.start(auto_update=auto_update)

    def is_running(self) -> bool:
        return self.managed_process.is_running() if self.managed_process else False

    def pid(self) -> int | None:
        return self.managed_process.pid() if self.managed_process else None

    def is_update_available(self) -> bool:
        try:
            return self.version_manager.is_update_available()
        except Exception as e:
            log.error(f"Failed to check for updates: {e}")
            return False
