from server_runner.steam.api.auth_info import AuthInfo
from server_runner.steam.api.rest_api_base import RESTSteamServerAPI
from server_runner.steam.api_registry import API_REGISTRY
from server_runner.steam.steam_app_id import SteamAppID


def create_game_api(
    *,
    app_id: int,
    base_url: str,
    auth_info: AuthInfo | None,
    timeout: int = 10,
) -> RESTSteamServerAPI:
    try:
        steam_id = SteamAppID(app_id)
    except ValueError as e:
        raise ValueError(f"Unsupported Steam server App ID: {app_id}") from e

    api_cls = API_REGISTRY.get(steam_id)
    if api_cls is None:
        raise ValueError(f"No API registered for App ID {steam_id}")

    return api_cls(
        base_url=base_url,
        auth_info=auth_info,
        timeout=timeout,
    )
