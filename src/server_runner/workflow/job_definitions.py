from collections.abc import Callable
from enum import Enum, auto
from typing import Literal, TypedDict

from server_runner.steam.managed_game_server import ManagedGameServer, ServerState
from server_runner.workflow.tasks import Task, TaskFactory


# ------------------------
# JobID enum
# ------------------------
class JobID(Enum):
    START = auto()
    UPDATE_START = auto()
    RESTART = auto()
    OOM = auto()
    UPDATE = auto()
    STOP = auto()


# ------------------------
# Optional schedule for a job
# ------------------------
class JobSchedule(TypedDict, total=False):
    times: list[str]  # e.g., [":00", ":15"]
    interval: Literal["minute", "hour", "day"]
    condition: Callable[[], bool]  # lambda returning bool


# ------------------------
# Job definition types
# ------------------------

TaskBuilder = Callable[[], Task]


class JobDef(TypedDict):
    priority: int
    tasks: list[TaskBuilder]
    schedule: JobSchedule | None  # optional scheduling info


JobDefs = dict[JobID, JobDef]  # <-- use enum as key


def get_job_definitions(server: ManagedGameServer) -> JobDefs:
    tf = TaskFactory(server)

    return {
        JobID.START: {
            "priority": 1,
            "tasks": [tf.start],
            "schedule": {
                "times": [":00"],
                "interval": "minute",
                "condition": lambda: server.state() is not ServerState.RUNNING,
            },
        },
        JobID.UPDATE_START: {
            "priority": 2,
            "tasks": [tf.update, tf.start],
            "schedule": None,  # manual only
        },
        JobID.RESTART: {
            "priority": 3,
            "tasks": [
                # Countdown with custom checkpoints: 5 min, 1 min, 30s
                lambda: tf.countdown(
                    "Restarting", delay_minutes=15, checkpoints=[300, 60, 30]
                ),
                tf.stop,
                tf.start,
            ],
            "schedule": {
                "times": ["05:45"],
                "interval": "day",
                "condition": lambda: server.state() is not ServerState.RUNNING,
            },
        },
        JobID.OOM: {
            "priority": 4,
            "tasks": [
                # Countdown with short, frequent checkpoints for quick OOM restart
                lambda: tf.countdown(
                    "OOM detected", delay_minutes=1, checkpoints=[60, 30, 15, 5]
                ),
                tf.stop,
                tf.start,
            ],
            "schedule": {
                "times": [":00", ":10", ":20", ":30", ":40", ":50"],
                "interval": "hour",
                "condition": lambda: server.is_out_of_memory(),
            },
        },
        JobID.UPDATE: {
            "priority": 5,
            "tasks": [
                # Countdown with custom checkpoints: 15min, 5 min, 1 min, 30s
                lambda: tf.countdown(
                    "Update incoming", delay_minutes=15, checkpoints=[600, 300, 60, 30]
                ),
                tf.stop,
                tf.update,
            ],
            "schedule": {
                "times": [":00", ":15", ":30", ":45"],
                "interval": "hour",
                "condition": lambda: server.update_available(),
            },
        },
        JobID.STOP: {
            "priority": 6,
            "tasks": [tf.stop],
            "schedule": None,  # manual only
        },
    }
