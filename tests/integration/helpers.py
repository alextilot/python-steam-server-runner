import os
import sys
import time
from collections.abc import Sequence
from textwrap import dedent

import psutil

PYTHON: str = sys.executable


def long_running_python_process() -> Sequence[str]:
    code = dedent(
        """
        import signal
        import time
        import sys

        def handler(signum, frame):
            sys.exit(0)

        signal.signal(signal.SIGTERM, handler)

        while True:
            time.sleep(0.1)
        """
    )
    return (PYTHON, "-c", code)


def crashing_python_process(exit_code: int = 42) -> Sequence[str]:
    return (PYTHON, "-c", f"import sys; sys.exit({exit_code})")


def parent_with_child_process() -> Sequence[str]:
    """
    Returns a command for a Python process that spawns a child
    that runs forever. Used to test recursive kill.
    """
    code = dedent(
        """
        import subprocess
        import sys
        import time

        # Spawn a long-running child
        subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(999)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Keep parent alive
        while True:
            time.sleep(0.1)
        """
    )
    return (PYTHON, "-c", code)


def wait_for_child_process(
    parent_pid: int, timeout: float = 2.0
) -> list[psutil.Process]:
    """
    Wait until the parent process has at least one child, or timeout.
    Returns the list of child processes.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            parent = psutil.Process(parent_pid)
            children = parent.children(recursive=True)
            if children:
                return children
        except psutil.NoSuchProcess:
            return []
        time.sleep(0.01)  # 10ms polling interval
    return []


def stdout_stderr_emitter() -> Sequence[str]:
    """
    Emits deterministic stdout and stderr, flushes,
    then blocks so the process stays alive.
    """
    code = dedent(
        """
        import sys
        import time

        print("hello stdout", flush=True)
        print("hello stderr", file=sys.stderr, flush=True)

        while True:
            time.sleep(0.1)
        """
    )
    return (PYTHON, "-c", code)


def process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
