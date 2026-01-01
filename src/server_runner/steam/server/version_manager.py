import subprocess

import requests
from jsonschema import ValidationError, validate

from server_runner.config.logging import get_logger
from server_runner.steam.server.steamcmd_schema import make_steamcmd_schema

log = get_logger()


class SteamServerVersionManager:
    """
    Handles fetching current and latest Steam game versions,
    and checking for updates.
    """

    def __init__(self, app_id: int):
        self.app_id = app_id
        self.steamcmd_schema = make_steamcmd_schema(self.app_id)

        # SteamCMD commands
        self.steamcmd_update_info = f"steamcmd +login anonymous +app_info_update 1 +app_status {self.app_id} +quit"
        self.steamcmd_update_game = (
            f"steamcmd +login anonymous +app_update {self.app_id} validate +quit"
        )

    def get_current_version(self) -> int | None:
        try:
            process = subprocess.run(
                f"{self.steamcmd_update_info} | grep -Eo '(BuildID )([0-9]*)' | grep -Eo '[0-9]*'",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            version = int(process.stdout.strip())
            return version
        except ValueError:
            log.error("ValueError: Cannot convert current version to integer")
            return None

    def get_latest_version(self) -> int | None:
        url = f"https://api.steamcmd.net/v1/info/{self.app_id}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            validate(instance=data, schema=self.steamcmd_schema)
            buildid = data["data"][self.app_id]["depots"]["branches"]["public"][
                "buildid"
            ]
            latest_version = int(buildid)
            return latest_version
        except (requests.RequestException, ValidationError, ValueError) as e:
            log.error(f"Failed to fetch latest version: {e}")
            return None

    def is_update_available(self) -> bool:
        current = self.get_current_version()
        latest = self.get_latest_version()
        if current is None or latest is None:
            return False
        if current != latest:
            log.info(f"Update available: {current} -> {latest}")
            return True
        return False

    def update(self) -> bool:
        log.info(f"Updating app {self.app_id} via SteamCMD...")
        process = subprocess.run(
            self.steamcmd_update_game,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        success = process.returncode == 0
        if success:
            log.info("Update completed successfully.")
        else:
            log.error("Update failed!")
        return success
