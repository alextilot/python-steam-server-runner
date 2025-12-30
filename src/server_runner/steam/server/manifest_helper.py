from pathlib import Path

import vdf  # type: ignore[reportUnknownMemberType]

from server_runner.config.logging import get_logger

log = get_logger()


class SteamManifestHelper:
    """
    Handles reading Steam app manifests to resolve game directories.
    Single source of truth for App ID -> game path.
    """

    STEAM_APPS_DIR = "steamapps"
    COMMON_DIR = "common"

    def __init__(self, steam_path: str):
        self.steam_path = Path(steam_path)
        self.steamapps_path = self.steam_path / self.STEAM_APPS_DIR
        if not self.steamapps_path.exists():
            raise FileNotFoundError(
                f"Steam 'steamapps' directory not found: {self.steamapps_path}"
            )

    def get_game_dir(self, app_id: int) -> Path:
        """
        Resolve the installation directory of a Steam game using its app manifest.

        Args:
            app_id: Steam App ID

        Returns:
            Path to the game's folder inside steamapps/common
        """
        manifest_path = self.steamapps_path / f"appmanifest_{app_id}.acf"
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Manifest not found for App ID {app_id}: {manifest_path}"
            )

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = vdf.load(f)
            installdir = data["AppState"]["installdir"]
        except Exception as e:
            raise ValueError(f"Failed to parse manifest {manifest_path}: {e}") from e

        game_dir = self.steamapps_path / self.COMMON_DIR / installdir
        if not game_dir.exists():
            raise FileNotFoundError(f"Game directory does not exist: {game_dir}")

        return game_dir
