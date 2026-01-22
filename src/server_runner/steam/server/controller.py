from server_runner.config.logging import get_logger
from server_runner.steam.app.steam_app_id import SteamAppID
from server_runner.steam.server.install_resolver import SteamInstallResolver
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
        steam_app_id: SteamAppID,
        resolver: SteamInstallResolver,
        server_arguments: list[str] | None = None,
    ):
        self.steam_app_id = steam_app_id
        self.server_arguments = server_arguments or []

        self.game_exe = resolver.get_game_executable()
        self.game_cmd = [str(self.game_exe)] + self.server_arguments

        self.proc = ManagedProcess(self.game_cmd)
        self.version_manager = SteamServerVersionManager(steam_app_id.value)

    # ---------- process management ----------
    def start(self, auto_update: bool = False) -> None:
        if self.is_running():
            log.warning(f"{self.steam_app_id.name} already running (PID {self.pid()})")
            return

        if auto_update and self.version_manager.is_update_available():
            log.info(f"Auto-update enabled, updating {self.steam_app_id.name}...")
            self.version_manager.update()

        self.proc.start()
        log.info(f"Started {self.steam_app_id.name} (PID {self.pid()})")

    def stop(self) -> None:
        self.proc.terminate(timeout=10)
        log.info(f"Stopped {self.steam_app_id.name}")

    def is_running(self) -> bool:
        return self.proc.is_running()

    def pid(self) -> int | None:
        return self.proc.pid()

    def get_memory_usage(self) -> float:
        return self.proc.get_process_memory_percent()

    def is_update_available(self) -> bool:
        try:
            return self.version_manager.is_update_available()
        except Exception as e:
            log.error(f"Failed to check for updates: {e}")
            return False

    def update(self) -> None:
        self.version_manager.update()
