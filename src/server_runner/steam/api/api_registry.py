from collections.abc import Mapping

from server_runner.steam.api.games.base_rest_api import RESTSteamServerAPI
from server_runner.steam.api.games.palworld_api import PalWorldAPI
from server_runner.steam.app.steam_app_id import SteamAppID

API_REGISTRY: Mapping[SteamAppID, type[RESTSteamServerAPI]] = {
    SteamAppID.PALWORLD_DEDICATED_SERVER: PalWorldAPI,
}
