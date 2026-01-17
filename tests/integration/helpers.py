import sys
import time

from server_runner.utils.managed_process import ManagedProcess

PYTHON = sys.executable


def sleep_cmd(seconds: float) -> list[str]:
    return [PYTHON, "-c", f"import time; time.sleep({seconds})"]


def exit_cmd(code: int) -> list[str]:
    return [PYTHON, "-c", f"raise SystemExit({code})"]


def ignore_sigterm_cmd() -> list[str]:
    return [
        PYTHON,
        "-c",
        """
import signal, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
time.sleep(10)
""",
    ]


def wait_for_exit(proc: ManagedProcess, timeout: float = 2.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not proc.is_running():
            return
        time.sleep(0.05)
    raise TimeoutError("process did not exit in time")
