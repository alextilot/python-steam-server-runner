from abc import ABC, abstractmethod
from dataclasses import dataclass

from server_runner.config.logging import get_logger
from server_runner.steam.game_server_manager import GameServerManager, ServerState

log = get_logger()


SECONDS_IN_A_MINUTE = 60


@dataclass
class TaskResult:
    success: bool
    message: str | None = None


class Task(ABC):
    def __init__(self, gsm: GameServerManager):
        self.gsm: GameServerManager = gsm

    @abstractmethod
    def run(self) -> TaskResult:
        raise NotImplementedError


class TaskStart(Task):
    def run(self) -> TaskResult:
        if self.gsm.state() is ServerState.RUNNING:
            return TaskResult(True, "Server already running")

        self.gsm.start()
        return TaskResult(True, "Server started")


class TaskStop(Task):
    def run(self) -> TaskResult:
        if self.gsm.state() is ServerState.STOPPED:
            return TaskResult(True, "Server already stopped")

        self.gsm.stop()
        return TaskResult(True, "Server stop requested")


class TaskUpdate(Task):
    def run(self) -> TaskResult:
        self.gsm.update()
        return TaskResult(True, "Update complete")


class TaskCountdown(Task):
    def __init__(
        self,
        gsm: GameServerManager,
        title: str,
        delay_minutes: int = 0,
    ) -> None:
        super().__init__(gsm)
        self.title = title
        self.total_seconds = delay_minutes * SECONDS_IN_A_MINUTE

    def run(self) -> TaskResult:
        remaining = self.total_seconds

        checkpoints = [5 * 60, 60, 30, 15]

        for checkpoint in checkpoints:
            if remaining <= checkpoint:
                continue

            self._announce(remaining)
            self.gsm.wait.sleep(remaining - checkpoint)
            remaining = checkpoint

        while remaining > 0:
            self._announce(remaining)
            self.gsm.wait.sleep(15)
            remaining -= 15

        return TaskResult(True, "Countdown completed")

    def _announce(self, seconds: int) -> None:
        if seconds >= SECONDS_IN_A_MINUTE:
            value = seconds // SECONDS_IN_A_MINUTE
            unit = "minutes"
        else:
            value = seconds
            unit = "seconds"

        self.gsm.announce(f"[{self.title}] restarting in {value} {unit}")


class TaskFactory:
    def __init__(self, gsm: GameServerManager) -> None:
        self.gsm = gsm

    def start(self) -> TaskStart:
        return TaskStart(self.gsm)

    def stop(self) -> TaskStop:
        return TaskStop(self.gsm)

    def update(self) -> TaskUpdate:
        return TaskUpdate(self.gsm)

    def countdown(self, title: str, minute_delay: int = 0) -> TaskCountdown:
        return TaskCountdown(self.gsm, title, minute_delay)
