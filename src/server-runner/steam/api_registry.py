from collections.abc import Mapping

from server_runner.steam.api.games.palworld_api import PalWorldAPI
from server_runner.steam.api.rest_api_base import RESTSteamServerAPI
from server_runner.steam.steam_app_id import SteamAppID

API_REGISTRY: Mapping[SteamAppID, type[RESTSteamServerAPI]] = {
    SteamAppID.PALWORLD_DEDICATED_SERVER: PalWorldAPI,
}
