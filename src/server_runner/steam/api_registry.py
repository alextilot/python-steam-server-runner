from collections.abc import Mapping

from api.games.palworld_api import PalWorldAPI
from api.rest_api_base import RESTSteamGameAPI
from constants.steam_app_id import SteamAppID

API_REGISTRY: Mapping[SteamAppID, type[RESTSteamGameAPI]] = {
    SteamAppID.PALWORLD: PalWorldAPI,
}
