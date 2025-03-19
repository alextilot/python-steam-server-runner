import logging
import time

from steam.palworld_api import PalWorldAPI
from steam.steam_game import SteamGame

log = logging.getLogger(__name__)


class ServerAction:
    def __init__(self, server_api: PalWorldAPI, game: SteamGame):
        self.server_api = server_api
        self.game = game

    def wait(self, seconds: int):
        time.sleep(seconds)

    def wait_for(self, condition, seconds=15):
        checks = 0
        while not condition() and checks < seconds:
            checks += 1
            self.wait(1)
        return not condition()

    def announce(self, message: str):
        self.server_api.announce(message)

    def save(self):
        self.server_api.save()

    def shutdown(self, message: str, delay: int):
        self.server_api.shutdown(message, delay)

    def stop(self):
        self.server_api.stop()

    def start(self):
        self.game.start()

    def update(self):
        self.game.update()

    def force_stop(self):
        self.game.stop()

    def is_running(self):
        return self.game.is_running()
