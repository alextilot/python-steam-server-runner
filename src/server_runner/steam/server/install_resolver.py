import sys
from pathlib import Path

import vdf  # type: ignore[reportUnknownMemberType]

from server_runner.config.logging import get_logger
from server_runner.steam.app.steam_app_id import SteamAppID

log = get_logger()


class SteamInstallResolver:
    """
    Resolves the installation directory of a Steam game.

    Exactly one of steam_path or install_dir must be provided:
    - steam_path: SteamCMD root for manifest-based resolution
    - install_dir: explicit game directory (force_install_dir)
    """

    STEAM_APPS_DIR = "steamapps"
    COMMON_DIR = "common"

    def __init__(
        self,
        steam_app_id: SteamAppID,
        *,
        steam_path: str | None = None,
        install_dir: str | None = None,
    ):
        self.steam_app_id = steam_app_id

        if steam_path and install_dir:
            raise ValueError("Provide either steam_path or install_dir, not both")
        if not steam_path and not install_dir:
            raise ValueError("One of steam_path or install_dir must be provided")

        # Manage all path logic internally
        self.install_dir = Path(install_dir) if install_dir else None
        self.steam_path = Path(steam_path) if steam_path else None
        self.steamapps_path = (
            (self.steam_path / self.STEAM_APPS_DIR) if self.steam_path else None
        )

        # Validate existence early
        if self.install_dir and not self.install_dir.exists():
            raise FileNotFoundError(
                f"Install directory does not exist: {self.install_dir}"
            )
        if self.steamapps_path and not self.steamapps_path.exists():
            raise FileNotFoundError(
                f"Steam 'steamapps' directory not found: {self.steamapps_path}"
            )

    @classmethod
    def from_install_dir(
        cls, steam_app_id: SteamAppID, install_dir: str
    ) -> "SteamInstallResolver":
        return cls(steam_app_id, install_dir=install_dir)

    @classmethod
    def from_steam(
        cls, steam_app_id: SteamAppID, steam_path: str
    ) -> "SteamInstallResolver":
        return cls(steam_app_id, steam_path=steam_path)

    def get_game_dir(self) -> Path:
        """
        Return the path to the game's installation directory.

        - Returns install_dir if provided (force_install_dir)
        - Otherwise resolves via steam_path + manifest
        """
        if self.install_dir:
            return self.install_dir

        assert self.steamapps_path is not None  # for type checkers

        manifest_path = self.steamapps_path / f"appmanifest_{self.steam_app_id}.acf"
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Manifest not found for App ID {self.steam_app_id}: {manifest_path}"
            )

        with open(manifest_path, encoding="utf-8") as f:
            data = vdf.load(f)

        installdir = data["AppState"]["installdir"]
        game_dir = self.steamapps_path / self.COMMON_DIR / installdir

        if not game_dir.exists():
            raise FileNotFoundError(
                f"Resolved game directory does not exist: {game_dir}"
            )

        return game_dir

    def get_game_executable(self) -> Path:
        """Return the expected shell script executable for the game"""
        game_dir = self.get_game_dir()
        base_name = game_dir.name

        if sys.platform.startswith("win"):
            exe = game_dir / f"{base_name}.exe"
        else:
            exe = game_dir / f"{base_name}.sh"

        if not exe.exists():
            raise FileNotFoundError(f"Game executable not found: {exe}")

        return exe
