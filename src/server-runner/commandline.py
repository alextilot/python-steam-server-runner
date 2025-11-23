import argparse
import logging
import sys
from typing import Optional, Tuple, TypedDict

log = logging.getLogger(__name__)


class StartArgs(TypedDict):
    username: str
    password: str
    steam_path: str
    app_id: int
    api: str
    game_name: str
    game_args: str


class CommandLine:
    def __init__(self):
        # Parse user arguments, Need username and password for server.
        self.parseArgs = argparse.ArgumentParser(
            prog="ServerRunner", description="Runs a server", epilog=""
        )
        self.parseArgs.add_argument(
            "--username", required=True, help="Username for steam server"
        )
        self.parseArgs.add_argument(
            "--password", required=True, help="Password for steam server"
        )
        self.parseArgs.add_argument("--steam_path", required=True, help="Steam path")
        self.parseArgs.add_argument(
            "--app_id", required=True, help="AppId for steam game"
        )
        self.parseArgs.add_argument("--api", required=True, help="Steam game api")
        self.parseArgs.add_argument(
            "--game_name", required=True, help="Steam game name"
        )

    def parse_start_args(self) -> StartArgs:
        args, other_args = self.parseArgs.parse_known_args()
        return {
            "username": args.username,
            "password": args.password,
            "steam_path": args.steam_path,
            "app_id": args.app_id,
            "api": args.api,
            "game_name": args.game_name,
            "game_args": " ".join(other_args),
        }

    def parse_user_input(self, input: str, process_command):
        first_space_index = input.find(" ")
        if first_space_index > -1:
            # Remove the @ and get the full word.
            first_word = input[:first_space_index]
            rest_of_string = input[first_space_index + 1 :]
            return process_command(first_word, rest_of_string)
        return process_command(input)

    def parse_command(self, process_command) -> Tuple[Optional[str], bool]:
        try:
            line = sys.stdin.readline().strip()
            if not line:
                return None, False
            output = self.parse_user_input(line, process_command)
            return output, False
        except KeyboardInterrupt:
            return None, True
        except SystemExit:
            return None, True
        except Exception as e:
            log.error(f"An error occured: {e}")
            return None, False
