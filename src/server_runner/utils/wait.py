import time
from collections.abc import Callable


class Wait:
    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def until(
        self, condition: Callable[[], bool], timeout: int, interval: float = 1.0
    ) -> bool:
        """
        Wait for a condition to become True.

        Args:
            condition: Callable returning a boolean.
            timeout: Maximum time to wait in seconds.
            interval: How often to check the condition.

        Returns:
            True if condition became True within timeout, False otherwise.
        """
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if condition():
                return True
            time.sleep(interval)
        return False
