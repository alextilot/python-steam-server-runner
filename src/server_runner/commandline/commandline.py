import argparse
from dataclasses import dataclass

from server_runner.config.logging import get_logger

log = get_logger()


@dataclass
class ServerConfig:
    app_id: int
    steam_path: str
    game_name: str
    game_args: list[str]
    api_username: str
    api_password: str
    api_base_url: str


class CommandLine:
    def __init__(self):
        # Parse user arguments, Need username and password for server.
        self.parseArgs = argparse.ArgumentParser(
            prog="ServerRunner", description="Runs a server", epilog=""
        )

        self.parseArgs.add_argument(
            "-i" "--app_id", required=True, help="AppId for steam game", type=int
        )
        self.parseArgs.add_argument(
            "-s", "--steam_path", required=True, help="Steam path", type=str
        )
        self.parseArgs.add_argument(
            "-n", "--game_name", help="Steam game name", type=str
        )

        self.parseArgs.add_argument(
            "-b", "--api_base_url", help="Base url for steam game api", type=str
        )
        self.parseArgs.add_argument(
            "-u",
            "--api_username",
            help="Username for steam game api",
            type=str,
        )
        self.parseArgs.add_argument(
            "-p",
            "--api_password",
            help="Password for steam game api",
            type=str,
        )

    def parse_server_config(self) -> ServerConfig:
        args, other_args = self.parseArgs.parse_known_args()
        return ServerConfig(
            app_id=args.app_id,
            steam_path=args.steam_path,
            game_name=args.game_name,
            game_args=other_args,
            api_username=args.api_username,
            api_password=args.api_password,
            api_base_url=args.api_base_url,
        )
