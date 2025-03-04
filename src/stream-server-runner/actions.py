import logging
import time
from enum import StrEnum

from steam.palworld_api import PalWorldAPI
from steam.steam_game import SteamGame

SECONDS_IN_A_MINUTE = 60


log = logging.getLogger(__name__)


class ActionType(StrEnum):
    UPDATE = "UPDATE"
    OUT_OF_MEMORY = "OUT_OF_MEMORY"
    RESTART = "RESTART"
    START = "START"
    FRESH_START = "FRESH_START"


class Action:
    def __init__(self, server_api: PalWorldAPI, game: SteamGame, delay_minutes=0):
        self.server_api = server_api
        self.game = game
        self.delay_minutes = delay_minutes

    def execute(self):
        raise NotImplementedError

    def format_countdown(self, minutes: int, seconds: int) -> tuple[int, str]:
        remainder = seconds // SECONDS_IN_A_MINUTE
        total_minutes = minutes + remainder
        if total_minutes > 0:
            return total_minutes, "minutes"
        return seconds, "seconds"

    def countdown_announce(self, title: str):
        minutes = self.delay_minutes
        seconds = 0

        if minutes > 0:
            minutes -= 1
            seconds += SECONDS_IN_A_MINUTE

        # Countdown every minute.
        while minutes > 0:
            value, unit = self.format_countdown(minutes, seconds)
            self.server_api.announce(f"{title} Restarting in {value} {unit}")
            minutes -= 1
            time.sleep(SECONDS_IN_A_MINUTE)

        # 1 minute remaining.
        if seconds == SECONDS_IN_A_MINUTE:
            value, unit = self.format_countdown(minutes, seconds)
            self.server_api.announce(f"{title} Restarting in {value} {unit}")
            seconds -= 15
            time.sleep(15)

        # Countdown every 15 seconds.
        while seconds >= 0:
            value, unit = self.format_countdown(minutes, seconds)
            self.server_api.announce(f"{title} Restarting in {value} {unit}")
            seconds -= 15
            time.sleep(15)

    def wait_for_shutdown(self, timer=60):
        checks = 0
        while self.game.is_running() and checks < timer:
            checks += 1
            time.sleep(1)
        return not self.game.is_running()


class ActionStart(Action):
    def execute(self):
        if not self.game.is_running():
            self.game.start()


class ActionOutOfMemory(Action):
    def execute(self):
        self.countdown_announce("[Emergency Restart]")

        self.server_api.save()
        self.server_api.shutdown("[Emergency Restart] Restarting ...", 10)

        if not self.wait_for_shutdown():
            log.error("Game failed to shutdown")
            return
        time.sleep(30)

        self.game.start()


class ActionRestart(Action):
    def execute(self):
        self.countdown_announce("[Scheduled Restart]")

        self.server_api.save()
        self.server_api.shutdown("[Scheduled Restart] Restarting ...", 10)

        if not self.wait_for_shutdown():
            log.error("Game failed to shutdown")
            return
        time.sleep(30)

        self.game.start()


class ActionFreshStart(Action):
    def execute(self):
        self.game.stop()
        # self.game.update()
        self.game.start()


class ActionUpdate(Action):
    def execute(self):
        self.countdown_announce("[New Update Available]")

        self.server_api.save()
        self.server_api.shutdown("[New Update Available] Restarting ...", 10)

        if not self.wait_for_shutdown():
            log.error("Game failed to shutdown")
            return
        time.sleep(30)

        self.game.update()
        self.game.start()
