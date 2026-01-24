from server_runner.steam.api.api_registry import API_REGISTRY
from server_runner.steam.api.auth_info import AuthInfo
from server_runner.steam.api.games.base_rest_api import RESTSteamServerAPI
from server_runner.steam.app.steam_app_id import SteamAppID


def create_game_api(
    steam_app_id: SteamAppID,
    *,
    base_url: str,
    auth_info: AuthInfo | None,
    timeout: int = 10,
) -> RESTSteamServerAPI:

    api_cls = API_REGISTRY.get(steam_app_id)
    if api_cls is None:
        raise ValueError(f"No API registered for App ID {steam_app_id.name}")

    return api_cls(
        base_url=base_url,
        auth_info=auth_info,
        timeout=timeout,
    )
