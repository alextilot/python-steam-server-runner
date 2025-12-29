from collections.abc import Mapping

from server_runner.constants.steam_app_id import SteamAppID
from server_runner.servers.api.games.palworld_api import PalWorldAPI
from server_runner.servers.api.rest_api_base import RESTSteamGameAPI

API_REGISTRY: Mapping[SteamAppID, type[RESTSteamGameAPI]] = {
    SteamAppID.PALWORLD: PalWorldAPI,
}
