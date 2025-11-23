import logging
import os.path
import subprocess
import sys

import psutil
import requests
from jsonschema import ValidationError, validate

log = logging.getLogger(__name__)

steamcmd_schema = {
    "type": "object",
    "required": ["data"],
    "properties": {
        "data": {
            "type": "object",
            "required": ["2394010"],
            "properties": {
                "2394010": {
                    "type": "object",
                    "required": ["depots"],
                    "properties": {
                        "depots": {
                            "type": "object",
                            "required": ["branches"],
                            "properties": {
                                "branches": {
                                    "type": "object",
                                    "required": ["public"],
                                    "properties": {
                                        "public": {
                                            "type": "object",
                                            "required": ["buildid"],
                                            "properties": {
                                                "buildid": {"type": "string"}
                                            },
                                        }
                                    },
                                }
                            },
                        },
                    },
                },
            },
        }
    },
}


def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


def _os_path_exists_raise(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError


class SteamGame:
    META_DATA_DIR = "steamapps"
    STEAM_APPS_DIR = "steamapps/common"

    def __init__(
        self,
        steam_path: str,
        app_id: str | int,
        game_name: str,
        server_arguments: str,
    ):
        self.steam_path = steam_path
        _os_path_exists_raise(self.steam_path)

        self.app_id = app_id
        self.game_name = game_name

        game_shell_script = os.path.join(
            steam_path, self.STEAM_APPS_DIR, game_name, f"{game_name}.sh"
        )
        _os_path_exists_raise(game_shell_script)

        self.game_command_start = f"{game_shell_script} {server_arguments}"
        self.steamcmd_update_game = (
            f"steamcmd +login anonymous +app_update {self.app_id} validate +quit"
        )
        self.steamcmd_update_info = f"steamcmd +login anonymous +app_info_update 1 +app_status {self.app_id} +quit"
        self.process = None

    def get_current_version(self) -> int | None:
        process = subprocess.run(
            f"{self.steamcmd_update_info} | grep -Eo '(BuildID )([0-9]*)' | grep -Eo '[0-9]*'",
            shell=True,
            stdout=subprocess.PIPE,
        )
        try:
            value = process.stdout.decode()
            result = int(value)
            return result
        except ValueError:
            log.error(f"ValueError: Cannot convert to integer")
            return None

    def get_latest_version(self) -> int | None:
        url = f"https://api.steamcmd.net/v1/info/{self.app_id}"
        try:
            response = requests.get(url)
            # Check if the request was successful (status code 200)
            response.raise_for_status()
            json_data = response.json()

            # Validate will raise exception if given json is not
            # what is described in schema.
            validate(instance=json_data, schema=steamcmd_schema)
            buildid = json_data["data"][self.app_id]["depots"]["branches"]["public"][
                "buildid"
            ]
            result = int(buildid)
            return result
        except requests.exceptions.HTTPError as e:
            log.error(f"HTTPError: https://api.steampowered.com: {e}")
            return None
        except requests.exceptions.RequestException as e:
            log.error(f"RequestException: https://api.steampowered.com: {e}")
            return None
        except ValidationError as e:
            log.error(f"ValidationError: https://api.steampowered.com: {e}")
            return None
        except ValueError:
            log.error(f"ValueError: Cannot convert to integer")
            return None
        except Exception as e:
            log.error(f"Exception: {e}")
            return None

    def is_update_available(self) -> bool:
        try:
            current_version = self.get_current_version()
            log.debug(f"current game version: {current_version}")
            latest_version = self.get_latest_version()
            log.debug(f"latest game version: {latest_version}")

            if None in (current_version, latest_version):
                return False

            value = current_version != latest_version
            if value:
                log.info(f"new update available!")
            return value

        except ValidationError as e:
            log.error(f"ValidationError: unable to correctly check versions {e}")
            return False

    def update(self) -> bool:
        log.debug(f"updating")
        process = subprocess.run(
            self.steamcmd_update_game,
            shell=True,
            stdout=sys.stdout,
            stderr=subprocess.STDOUT,
        )
        return process.returncode == 0

    def start(self):
        log.debug(f"starting")
        self.process = subprocess.Popen(
            self.game_command_start,
            shell=True,
            stdout=sys.stdout,
            stderr=subprocess.STDOUT,
        )

    def stop(self):
        if self.process is None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=10)  # wait 10 seconds
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()

    def is_running(self):
        process = subprocess.run(
            f'pgrep -fa "{self.game_command_start}"',
            shell=True,
            stdout=subprocess.PIPE,
        )
        lines = process.stdout.decode().splitlines()
        return len(lines) > 1
