import logging

import psutil

SYSTEM_MEMORY_THRESHOLD = 95.0


log = logging.getLogger(__name__)


def get_memory_usage_percent() -> float:
    return psutil.virtual_memory().percent


class System:
    def is_out_of_memory(self):
        percent = get_memory_usage_percent()
        log.debug(
            f"Memory usage 'current: {percent}% threshold: {SYSTEM_MEMORY_THRESHOLD}%'"
        )
        return percent >= SYSTEM_MEMORY_THRESHOLD
