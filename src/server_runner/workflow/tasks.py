from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from server_runner.config.logging import get_logger
from server_runner.steam.managed_game_server import ManagedGameServer, ServerState

log = get_logger()


SECONDS_IN_A_MINUTE = 60


@dataclass
class TaskResult:
    success: bool
    message: str | None = None


class Task(ABC):
    def __init__(self, server: ManagedGameServer):
        self.server: ManagedGameServer = server

    @abstractmethod
    def run(self) -> TaskResult:
        raise NotImplementedError


class TaskStart(Task):
    def run(self) -> TaskResult:
        if self.server.state() is ServerState.RUNNING:
            return TaskResult(True, "Server already running")

        self.server.start()
        return TaskResult(True, "Server started")


class TaskStop(Task):
    def run(self) -> TaskResult:
        if self.server.state() is ServerState.STOPPED:
            return TaskResult(True, "Server already stopped")

        self.server.stop()
        return TaskResult(True, "Server stop requested")


class TaskUpdate(Task):
    def run(self) -> TaskResult:
        self.server.update()
        return TaskResult(True, "Update complete")


class TaskCountdown(Task):
    def __init__(
        self,
        server: ManagedGameServer,
        title: str,
        delay_minutes: int = 0,
        checkpoints: Sequence[int] | None = None,  # seconds
    ) -> None:
        super().__init__(server)
        self.title = title
        self.total_seconds = delay_minutes * SECONDS_IN_A_MINUTE
        # Default checkpoints: 5min, 1min, 30s, 15s
        self.checkpoints = sorted(checkpoints or [5 * 60, 60, 30, 15], reverse=True)

    def run(self) -> TaskResult:
        remaining = self.total_seconds

        while remaining > 0:
            # Announce if we are at or below a checkpoint
            for cp in self.checkpoints:
                if remaining <= cp:
                    self._announce(remaining)
                    self.checkpoints.remove(cp)
                    break

            # Sleep a small interval (max 15s) or remaining time
            sleep_time = min(15, remaining)
            self.server.wait.sleep(sleep_time)
            remaining -= sleep_time

        return TaskResult(True, "Countdown completed")

    def _announce(self, seconds: int) -> None:
        if seconds >= SECONDS_IN_A_MINUTE:
            value = seconds // SECONDS_IN_A_MINUTE
            unit = "minutes" if value > 1 else "minute"
        else:
            value = seconds
            unit = "seconds" if value > 1 else "second"

        self.server.announce(f"[{self.title}] restarting in {value} {unit}")


class TaskFactory:
    def __init__(self, server: ManagedGameServer) -> None:
        self.server = server

    def start(self) -> TaskStart:
        return TaskStart(self.server)

    def stop(self) -> TaskStop:
        return TaskStop(self.server)

    def update(self) -> TaskUpdate:
        return TaskUpdate(self.server)

    def countdown(
        self,
        title: str,
        delay_minutes: int = 0,
        checkpoints: Sequence[int] | None = None,
    ) -> TaskCountdown:
        return TaskCountdown(self.server, title, delay_minutes, checkpoints)
