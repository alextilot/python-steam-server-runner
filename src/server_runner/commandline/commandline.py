import argparse
from dataclasses import dataclass

from config.logging import get_logger

log = get_logger()


@dataclass
class ServerConfig:
    username: str
    password: str
    api_base_url: str
    app_id: int
    steam_path: str
    game_name: str
    game_args: list[str]


class CommandLine:
    def __init__(self):
        # Parse user arguments, Need username and password for server.
        self.parseArgs = argparse.ArgumentParser(
            prog="ServerRunner", description="Runs a server", epilog=""
        )
        self.parseArgs.add_argument(
            "-u",
            "--username",
            required=True,
            help="Username for steam server",
            type=str,
        )
        self.parseArgs.add_argument(
            "-p",
            "--password",
            required=True,
            help="Password for steam server",
            type=str,
        )
        self.parseArgs.add_argument(
            "-e", "--api_base_url", required=True, help="Steam game api", type=str
        )
        self.parseArgs.add_argument(
            "-i" "--app_id", required=True, help="AppId for steam game", type=int
        )
        self.parseArgs.add_argument(
            "-s", "--steam_path", required=True, help="Steam path", type=str
        )
        self.parseArgs.add_argument(
            "-n", "--game_name", required=True, help="Steam game name", type=str
        )

    def parse_server_config(self) -> ServerConfig:
        args, other_args = self.parseArgs.parse_known_args()
        return ServerConfig(
            username=args.username,
            password=args.password,
            api_base_url=args.api_base_url,
            app_id=args.app_id,
            steam_path=args.steam_path,
            game_name=args.game_name,
            game_args=other_args,
        )
