# ruff: noqa: S603
# S603: subprocess calls in this module execute trusted, internal commands only.
# Command inputs are not user-controlled and are validated at the call sites.

import subprocess

import requests
from jsonschema import ValidationError, validate

from server_runner.config.logging import get_logger
from server_runner.steam.server.steamcmd_schema import make_steamcmd_schema

log = get_logger()

STEAMCMD_PATH = "steamcmd"


class SteamServerVersionManager:
    """
    Handles fetching current and latest Steam game versions,
    and checking for updates.
    """

    def __init__(self, app_id: int):
        self.app_id = app_id
        self.steamcmd_schema = make_steamcmd_schema(self.app_id)

    def get_current_version(self) -> int | None:
        try:
            process = subprocess.run(
                [
                    STEAMCMD_PATH,
                    "+login",
                    "anonymous",
                    "+app_info_update",
                    "1",
                    "+app_status",
                    str(self.app_id),
                    "+quit",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            for line in process.stdout.splitlines():
                if "BuildID" in line:
                    _, build_id = line.split("BuildID", 1)
                    return int(build_id.strip())

        except (subprocess.CalledProcessError, ValueError) as e:
            log.error(f"Failed to get current version: {e}")

        return None

    def get_latest_version(self) -> int | None:
        url = f"https://api.steamcmd.net/v1/info/{self.app_id}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            validate(instance=data, schema=self.steamcmd_schema)
            buildid = data["data"][str(self.app_id)]["depots"]["branches"]["public"][
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
            [
                STEAMCMD_PATH,
                "+login",
                "anonymous",
                "+app_update",
                str(self.app_id),
                "validate",
                "+quit",
            ],
            capture_output=True,
            text=True,
        )

        if process.returncode == 0:
            log.info("Update completed successfully.")
            return True

        log.error(process.stderr.strip() or "Update failed")
        return False
