import argparse
from dataclasses import dataclass

from server_runner.config.logging import get_logger
from server_runner.steam.api.auth_info import AuthInfo, PasswordAuth, TokenAuth

log = get_logger()


@dataclass
class ServerConfig:
    app_id: int
    steam_path: str
    game_args: list[str]
    api_base_url: str
    auth_type: str
    auth_info: AuthInfo | None


class CommandLine:
    def __init__(self):
        self.parseArgs = argparse.ArgumentParser(
            prog="ServerRunner", description="Runs a server", epilog=""
        )

        # Steam/game arguments
        self.parseArgs.add_argument(
            "--app-id", required=True, type=int, help="App ID for the Steam game"
        )
        self.parseArgs.add_argument(
            "--steam-path", required=True, type=str, help="Path to Steam installation"
        )

        # API arguments
        self.parseArgs.add_argument(
            "--api-base-url",
            required=True,
            type=str,
            help="Base URL for the Steam game API",
        )

        # Auth type
        self.parseArgs.add_argument(
            "--auth-type",
            choices=["basic", "token"],
            default="basic",
            help="Type of API authentication",
        )

        # Generic auth fields
        self.parseArgs.add_argument(
            "--api-username", type=str, help="Username for basic auth"
        )
        self.parseArgs.add_argument(
            "--api-password", type=str, help="Password for basic auth"
        )
        self.parseArgs.add_argument(
            "--api-token", type=str, help="Token for token-based auth"
        )

    def parse_server_config(self) -> ServerConfig:
        args, other_args = self.parseArgs.parse_known_args()

        auth_info: AuthInfo | None = None
        if args.auth_type == "basic":
            if not args.api_username or not args.api_password:
                raise ValueError("Username and password are required for basic auth")
            auth_info = PasswordAuth(
                username=args.api_username, password=args.api_password
            )
        elif args.auth_type == "token":
            if not args.api_token:
                raise ValueError("Token is required for token auth")
            auth_info = TokenAuth(token=args.api_token)

        return ServerConfig(
            app_id=args.app_id,
            steam_path=args.steam_path,
            game_args=other_args,
            api_base_url=args.api_base_url,
            auth_type=args.auth_type,
            auth_info=auth_info,
        )
