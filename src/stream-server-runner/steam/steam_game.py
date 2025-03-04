import logging
import os.path
import subprocess
import sys
from enum import Enum

import psutil
from jsonschema import ValidationError, validate
from utils.parse_files import read_acf_file

log = logging.getLogger(__name__)

steampowered_schema = {
    "type": "object",
    "required": ["response"],
    "properties": {
        "response": {
            "type": "object",
            "required": ["success", "up_to_date", "version_is_listable"],
            "properties": {
                "success": {"type": "boolean"},
                "up_to_date": {"type": "boolean"},
                "version_is_listable": {"type": "boolean"},
            },
        }
    },
}

appmanifest_schema = {
    "type": "object",
    "required": ["AppState"],
    "properties": {
        "AppState": {
            "type": "object",
            "required": ["buildid", "StateFlags"],
            "properties": {
                "buildid": {"type": "string"},
                "StateFlags": {"type": "string"},
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


class AppState(Enum):
    STATE_INVALID = 0
    STATE_UNINSTALLED = 1
    STATE_UPDATE_REQUIRED = 2
    STATE_FULLY_INSTALLED = 4
    STATE_ENCRYPTED = 8
    STATE_LOCKED = 16
    STATE_FILES_MISSING = 32
    STATE_APP_RUNNING = 64
    STATE_FILES_CORRUPT = 128
    STATE_UPDATE_RUNNING = 256
    STATE_UPDATE_PAUSED = 512
    STATE_UPDATE_STARTED = 1024
    STATE_UNINSTALLING = 2048
    STATE_BACKUP_RUNNING = 4096
    STATE_RECONFIGURING = 65536
    STATE_VALIDATING = 131072
    STATE_ADDING_FILES = 262144
    STATE_PREALLOCATING = 524288
    STATE_DOWNLOADING = 1048576
    STATE_STAGING = 2097152
    STATE_COMMITTING = 4194304
    STATE_UPDATE_STOPPING = 8388608


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

        self.meta_data_file_path = os.path.join(
            steam_path, self.META_DATA_DIR, f"appmanifest_{app_id}.acf"
        )
        _os_path_exists_raise(self.meta_data_file_path)

        game_shell_script = os.path.join(
            steam_path, self.STEAM_APPS_DIR, game_name, f"{game_name}.sh"
        )
        _os_path_exists_raise(game_shell_script)

        self.game_command_start = f"{game_shell_script} {server_arguments}"
        self.game_command_update = (
            f"steamcmd +login anonymous +app_update {app_id} validate +quit"
        )
        self.game_command_info_update = (
            f"steamcmd +login anonymous +app_info_update 1 +app_status {app_id} +quit"
        )
        self.process = None

    # def get_buildid(self) -> str | None:
    #     file_data = read_acf_file(self.meta_data_file_path)
    #     if file_data == None:
    #         return None
    #     try:
    #         validate(instance=file_data, schema=appmanifest_schema)
    #         code = file_data["AppState"]["buildid"]
    #         return code
    #     except ValidationError as e:
    #         log.error(
    #             f"ValidationError: unable to parse file for buildid '{self.meta_data_file_path}' {e}"
    #         )
    #         return None
    #
    # def old_is_latest(self) -> bool:
    #     version = self.get_buildid()
    #     log.info(f"Server game version: {version}")
    #     if version == None:
    #         log.error(f"Unable to get server game version")
    #         return True
    #
    #     url = f"https://api.steampowered.com/ISteamApps/UpToDateCheck/v1/?appid={self.app_id}&version={version}"
    #     try:
    #         response = requests.get(url)
    #         # Check if the request was successful (status code 200)
    #         response.raise_for_status()
    #         json_data = response.json()
    #
    #         # Validate will raise exception if given json is not
    #         # what is described in schema.
    #         validate(instance=json_data, schema=steampowered_schema)
    #         is_latest = json_data["response"]["up_to_date"]
    #         log.info(f"Game is latest: {is_latest}")
    #         return is_latest
    #
    #     except requests.exceptions.HTTPError as e:
    #         log.error(f"HTTPError: https://api.steampowered.com: {e}")
    #         return True
    #     except requests.exceptions.RequestException as e:
    #         log.error(f"RequestException: https://api.steampowered.com: {e}")
    #         return True
    #     except ValidationError as e:
    #         log.error(f"ValidationError: https://api.steampowered.com: {e}")
    #         return True

    def is_update_available(self) -> bool:
        log.debug(f"is update available command: {self.game_command_info_update}")
        subprocess.run(
            self.game_command_info_update,
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        file_data = read_acf_file(self.meta_data_file_path)
        if file_data == None:
            return False
        try:
            validate(instance=file_data, schema=appmanifest_schema)
            code = file_data["AppState"]["StateFlags"]
            code = int(code)
            log.debug(f"AppState.StateFlags: {code} {AppState(code)}")
            return code == AppState.STATE_UPDATE_REQUIRED
        except ValidationError as e:
            log.error(
                f"ValidationError: unable to parse file for buildid '{self.meta_data_file_path}' {e}"
            )
            return False

    def update(self) -> bool:
        log.debug(f"update command: {self.game_command_update}")
        process = subprocess.run(
            self.game_command_update,
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return process.returncode == 0

    def start(self):
        log.debug(f"start command: {self.game_command_start}")
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
        output = subprocess.check_output(
            f'pgrep -fa "{self.game_command_start}"', shell=True
        ).decode()
        lines = output.splitlines()
        return len(lines) > 1
