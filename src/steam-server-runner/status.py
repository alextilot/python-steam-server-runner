import logging

from steam.palworld_api import PalWorldAPI
from steam.steam_game import SteamGame
from utils.system import System

log = logging.getLogger(__name__)


class Status:
    def __init__(
        self,
        server_api: PalWorldAPI,
        game: SteamGame,
        system: System,
    ):
        self.server_api = server_api
        self.game = game
        self.system = system

    def is_update_available(self) -> bool:
        log.debug("checking for available update")
        return self.game.is_update_available()

    def has_memory_leak(self) -> bool:
        log.debug("checking for memory leaks")
        return self.game.is_running() and self.system.is_out_of_memory()

    def is_game_running(self) -> bool:
        log.debug("checking for running game")
        return self.game.is_running()

    def is_game_stopped(self) -> bool:
        log.debug("checking for stopped game")
        return not self.game.is_running()
