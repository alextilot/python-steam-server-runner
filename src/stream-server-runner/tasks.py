import logging

from server_action import ServerAction

log = logging.getLogger(__name__)


SECONDS_IN_A_MINUTE = 60


class Task:
    def __init__(self, server_action: ServerAction):
        self.server = server_action

    def run(self):
        raise NotImplementedError


class TaskStart(Task):
    def run(self):
        if not self.server.is_running():
            self.server.start()


class TaskStop(Task):
    def run(self):
        self.server.save()
        self.server.shutdown("Shuting down ...", 5)

        # Wait for server to shutdown.
        not_running = lambda: not self.server.is_running()
        self.server.wait_for(not_running, 60)
        if self.server.is_running():
            log.error("Game still running, forcing stop.")
            self.server.force_stop()
            self.server.wait(30)


class TaskUpdate(Task):
    def run(self):
        self.server.update()


class TaskCountdown(Task):
    def __init__(self, server_action: ServerAction, title: str, delay_minutes=0):
        super().__init__(server_action)
        self.title = title
        self.delay_minutes = delay_minutes
        self.delay_seconds = 0
        if delay_minutes > 0:
            self.delay_minutes = delay_minutes - 1
            self.delay_seconds = SECONDS_IN_A_MINUTE

    def format(self, minutes: int, seconds: int) -> tuple[int, str]:
        remainder = seconds // SECONDS_IN_A_MINUTE
        total_minutes = minutes + remainder
        if total_minutes > 0:
            return total_minutes, "minutes"
        return seconds, "seconds"

    def run(self):
        minutes = self.delay_minutes
        seconds = self.delay_seconds
        # Countdown every minute.
        while minutes > 0:
            value, unit = self.format(minutes, seconds)
            self.server.announce(f"[{self.title}] restarting in {value} {unit}")
            self.server.wait(SECONDS_IN_A_MINUTE)
            minutes -= 1

        # 1 minute remaining.
        if seconds == SECONDS_IN_A_MINUTE:
            value, unit = self.format(minutes, seconds)
            self.server.announce(f"[{self.title}] restarting in {value} {unit}")
            self.server.wait(15)
            seconds -= 15

        # Countdown every 15 seconds.
        while seconds >= 0:
            value, unit = self.format(minutes, seconds)
            self.server.announce(f"[{self.title}] restarting in {value} {unit}")
            self.server.wait(15)
            seconds -= 15


class TaskFactory:
    def __init__(self, server_action: ServerAction):
        self.server_action = server_action

    def start(self):
        return TaskStart(self.server_action)

    def stop(self):
        return TaskStop(self.server_action)

    def update(self):
        return TaskUpdate(self.server_action)

    def countdown(self, title: str, minute_delay=0):
        return TaskCountdown(self.server_action, title, minute_delay)
