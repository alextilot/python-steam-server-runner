from server_runner.commandline.commandline import ServerConfig
from server_runner.steam.api.create_game_api import create_game_api
from server_runner.steam.app.steam_app_id import get_steam_app_id
from server_runner.steam.game_server_manager import GameServerManager
from server_runner.steam.server.controller import SteamServerController
from server_runner.steam.server.install_resolver import SteamInstallResolver
from server_runner.utils.wait import Wait


def create_game_server_manager(config: ServerConfig) -> GameServerManager:
    steam_app_id = get_steam_app_id(config.app_id)

    resolver = SteamInstallResolver(
        steam_app_id, steam_path=config.steam_path, install_dir=config.install_dir
    )

    controller = SteamServerController(steam_app_id, resolver, config.game_args)

    api = create_game_api(
        steam_app_id, base_url=config.api_base_url, auth_info=config.auth_info
    )

    waiter = Wait()

    return GameServerManager(controller, api, waiter)
