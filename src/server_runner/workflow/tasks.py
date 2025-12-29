from servers.game_server_manager import GameServerManager

from server_runner.config.logging import get_logger

log = get_logger()


SECONDS_IN_A_MINUTE = 60


class Task:
    def __init__(self, gsm: GameServerManager):
        self.gsm: GameServerManager = gsm

    def do(self) -> None:
        raise NotImplementedError


class TaskStart(Task):
    def do(self) -> None:
        if not self.gsm.is_running():
            self.gsm.start()


class TaskStop(Task):
    def do(self) -> None:
        self.gsm.save()
        self.gsm.shutdown("Shuting down ...", 5)

        # Wait for server to shutdown.
        def not_running():
            return not self.gsm.is_running()

        self.gsm.wait_for(not_running, 60)
        if self.gsm.is_running():
            log.error("Game still running, forcing stop.")
            self.gsm.force_stop()
            self.gsm.wait(30)


class TaskRestartWithUpdate(Task):
    """Restart the server, applying any available updates."""

    def do(self) -> None:
        self.gsm.restart(auto_update=True)


class TaskCountdown(Task):
    def __init__(
        self, server_action: GameServerManager, title: str, delay_minutes: int = 0
    ) -> None:
        super().__init__(server_action)
        self.title = title
        if delay_minutes > 0:
            self.delay_minutes = delay_minutes - 1
            self.delay_seconds = SECONDS_IN_A_MINUTE
        else:
            self.delay_minutes = delay_minutes
            self.delay_seconds = 0

    def format(self, minutes: int, seconds: int) -> tuple[int, str]:
        remainder = seconds // SECONDS_IN_A_MINUTE
        total_minutes = minutes + remainder
        if total_minutes > 0:
            return total_minutes, "minutes"
        return seconds, "seconds"

    def do(self) -> None:
        minutes = self.delay_minutes
        seconds = self.delay_seconds
        # Countdown every minute.
        while minutes > 0:
            value, unit = self.format(minutes, seconds)
            self.gsm.announce(f"[{self.title}] restarting in {value} {unit}")
            self.gsm.wait(SECONDS_IN_A_MINUTE)
            minutes -= 1

        # 1 minute remaining.
        if seconds == SECONDS_IN_A_MINUTE:
            value, unit = self.format(minutes, seconds)
            self.gsm.announce(f"[{self.title}] restarting in {value} {unit}")
            self.gsm.wait(15)
            seconds -= 15

        # Countdown every 15 seconds.
        while seconds >= 0:
            value, unit = self.format(minutes, seconds)
            self.gsm.announce(f"[{self.title}] restarting in {value} {unit}")
            self.gsm.wait(15)
            seconds -= 15


class TaskFactory:
    def __init__(self, gsm: GameServerManager) -> None:
        self.gsm = gsm

    def start(self) -> TaskStart:
        return TaskStart(self.gsm)

    def stop(self) -> TaskStop:
        return TaskStop(self.gsm)

    def restart_with_update(self) -> TaskRestartWithUpdate:
        return TaskRestartWithUpdate(self.gsm)

    def countdown(self, title: str, minute_delay: int = 0) -> TaskCountdown:
        return TaskCountdown(self.gsm, title, minute_delay)
