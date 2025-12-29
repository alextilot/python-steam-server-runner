from api.rest_api_base import RESTSteamGameAPI
from api_registry import API_REGISTRY
from constants.steam_app_id import SteamAppID


def create_game_api(
    *,
    app_id: int,
    base_url: str,
    username: str,
    password: str,
    timeout: int = 10,
) -> RESTSteamGameAPI:
    try:
        steam_id = SteamAppID(app_id)
    except ValueError as e:
        raise ValueError(f"Unsupported Steam server App ID: {app_id}") from e

    api_cls = API_REGISTRY.get(steam_id)
    if api_cls is None:
        raise ValueError(f"No API registered for App ID {steam_id}")

    return api_cls(
        base_url=base_url,
        username=username,
        password=password,
        timeout=timeout,
    )
