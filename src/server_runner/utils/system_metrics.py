import logging
from collections.abc import Callable

import psutil

SYSTEM_MEMORY_THRESHOLD = 95.0


log = logging.getLogger(__name__)


def get_memory_usage_percent() -> float:
    return psutil.virtual_memory().percent


class SystemMetrics:
    def __init__(
        self, max_memory_usage: float, get_current_memory_usage: Callable[[], float]
    ):
        self.max_memory_usage = max_memory_usage
        self.get_current_memory_usage = get_current_memory_usage

    def is_out_of_memory(self):
        current_memory_usage = self.get_current_memory_usage()
        log.debug(
            f"Memory usage 'current: {current_memory_usage}% threshold: {self.max_memory_usage}%'"
        )
        return current_memory_usage >= self.max_memory_usage
