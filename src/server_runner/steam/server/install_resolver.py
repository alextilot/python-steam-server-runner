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
    - steam_path: Steam root for manifest-based resolution
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
            raise ValueError("Provide either steam_path or install_dir, not both.")
        if not steam_path and not install_dir:
            raise ValueError("One of steam_path or install_dir must be provided.")

        self.install_dir = Path(install_dir) if install_dir else None
        self.steam_path = Path(steam_path) if steam_path else None

        self._validate_paths()

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

    def _validate_paths(self) -> None:
        """Ensure provided paths exist."""
        if self.install_dir and not self.install_dir.exists():
            raise FileNotFoundError(
                f"Install directory does not exist: {self.install_dir}"
            )
        if self.steam_path and not self.steam_path.exists():
            raise FileNotFoundError(
                f"Steam directory does not exist: {self.steam_path}"
            )

    def _read_manifest(self, root: Path) -> str:
        """Read the install directory name from the manifest."""
        manifest = root / self.STEAM_APPS_DIR / f"appmanifest_{self.steam_app_id}.acf"
        if not manifest.exists():
            raise FileNotFoundError(
                f"Manifest not found for App ID {self.steam_app_id}: {manifest}"
            )

        with open(manifest, encoding="utf-8") as f:
            data = vdf.load(f)
        return data["AppState"]["installdir"]

    def get_game_dir(self) -> tuple[Path, str]:
        """
        Return the game's installation directory path and name.
        Resolves from install_dir if provided, otherwise via steam_path + manifest.
        """
        if self.install_dir:
            name = self._read_manifest(self.install_dir)
            return self.install_dir, name

        assert self.steam_path is not None
        name = self._read_manifest(self.steam_path)
        game_dir = self.steam_path / self.STEAM_APPS_DIR / self.COMMON_DIR / name

        if not game_dir.exists():
            raise FileNotFoundError(
                f"Resolved game directory does not exist: {game_dir}"
            )

        return game_dir, name

    def get_game_executable(self) -> Path:
        """Return the expected game executable path."""
        game_dir, name = self.get_game_dir()
        exe = (
            game_dir / f"{name}.exe"
            if sys.platform.startswith("win")
            else game_dir / f"{name}.sh"
        )

        if not exe.exists():
            raise FileNotFoundError(f"Game executable not found: {exe}")

        return exe
