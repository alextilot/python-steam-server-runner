import argparse
from dataclasses import dataclass

from server_runner.config.logging import get_logger

log = get_logger()


@dataclass
class ServerConfig:
    username: str
    password: str
    steam_path: str
    app_id: int
    api: str
    game_name: str
    game_args: list[str]


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

    def parse_server_config(self) -> ServerConfig:
        args, other_args = self.parseArgs.parse_known_args()
        return ServerConfig(
            username=args.username,
            password=args.password,
            steam_path=args.steam_path,
            app_id=args.app_id,
            api=args.api,
            game_name=args.game_name,
            game_args=other_args,
        )
