from collections.abc import Callable
from enum import Enum, auto
from typing import Literal, TypedDict

from server_runner.steam.game_server_manager import GameServerManager
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


def get_job_definitions(gsm: GameServerManager) -> JobDefs:
    tf = TaskFactory(gsm)

    return {
        JobID.START: {
            "priority": 1,
            "tasks": [tf.start],
            "schedule": {
                "times": [":00"],
                "interval": "minute",
                "condition": lambda: gsm.state() != gsm.ServerState.RUNNING,
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
                lambda: tf.countdown("Restarting", 15),
                tf.stop,
                tf.start,
            ],
            "schedule": {
                "times": ["05:45"],
                "interval": "day",
                "condition": lambda: gsm.state() == gsm.ServerState.RUNNING,
            },
        },
        JobID.OOM: {
            "priority": 4,
            "tasks": [
                lambda: tf.countdown("OOM detected", 5),
                tf.stop,
                tf.start,
            ],
            "schedule": {
                "times": [":00", ":10", ":20", ":30", ":40", ":50"],
                "interval": "hour",
                "condition": lambda: gsm.is_out_of_memory(),
            },
        },
        JobID.UPDATE: {
            "priority": 5,
            "tasks": [
                lambda: tf.countdown("Update incoming", 15),
                tf.stop,
                tf.update,
            ],
            "schedule": {
                "times": [":00", ":15", ":30", ":45"],
                "interval": "hour",
                "condition": lambda: gsm.update_available(),
            },
        },
        JobID.STOP: {
            "priority": 6,
            "tasks": [tf.stop],
            "schedule": None,  # manual only
        },
    }
