from enum import Enum, auto


class JobID(Enum):
    START = auto()
    UPDATE_START = auto()
    RESTART = auto()
    OOM = auto()
    UPDATE = auto()
    STOP = auto()
