import logging

from steam.game_server_manager import GameServerManager
from utils.system_metrics import SystemMetrics

log = logging.getLogger(__name__)


class StatusManager:
    def __init__(
        self,
        gsm: GameServerManager,
        system: SystemMetrics,
    ):
        self.gsm = gsm
        self.system = system

    def is_update_available(self) -> bool:
        log.debug("checking for available update")
        return self.gsm.is_update_available()

    def has_memory_leak(self) -> bool:
        log.debug("checking for memory leaks")
        return self.gsm.is_running() and self.system.is_out_of_memory()

    def is_game_running(self) -> bool:
        log.debug("checking for running game")
        return self.gsm.is_running()

    def is_game_stopped(self) -> bool:
        log.debug("checking for stopped game")
        return not self.gsm.is_running()
