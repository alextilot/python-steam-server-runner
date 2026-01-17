import os
import signal
import subprocess
import time
from collections.abc import Sequence
from contextlib import suppress
from subprocess import Popen

import psutil


class ManagedProcess:
    def __init__(
        self,
        command: Sequence[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ):
        self.command = command
        self.cwd = cwd
        self.env = env
        self._proc: Popen[str] | None = None

    # ---------- lifecycle ----------

    def start(self) -> None:
        """
        Start the process, streaming output to the terminal.
        """
        if self.is_running():
            raise RuntimeError("Process already started")

        self._proc = subprocess.Popen(  # noqa: S603
            self.command,
            cwd=self.cwd,
            env=self.env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
            text=True,
        )

    def terminate(self, timeout: float = 5.0, sig: int = signal.SIGTERM) -> None:
        """
        Gracefully terminate the process using SIGTERM.
        Falls back to kill() if timeout expires.
        """
        if not self._proc or not self.is_running():
            self._proc = None
            return

        try:
            os.killpg(self._proc.pid, sig)
            self._proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.kill()
        except ProcessLookupError:
            pass
        finally:
            self._proc = None

    def kill(self) -> None:
        """
        Kill the process and all child processes using psutil.
        """
        if not self._proc or not self.is_running():
            self._proc = None
            return

        try:
            parent = psutil.Process(self._proc.pid)
            children = parent.children(recursive=True)
            for child in children:
                with suppress(psutil.NoSuchProcess):
                    child.kill()

            with suppress(psutil.NoSuchProcess):
                parent.kill()
                parent.wait(timeout=5)
        except psutil.NoSuchProcess:
            pass
        finally:
            self._proc = None

    def restart(self, delay: float = 0.5) -> None:
        """
        Restart the process by terminating and starting it again.
        """
        if self.is_running():
            self.terminate()
            time.sleep(delay)
        self.start()

    # ---------- inspection ----------

    def is_running(self) -> bool:
        """
        Return True if the process is currently running.
        Handles processes that have exited unexpectedly.
        """
        if self._proc is None:
            return False
        return self._proc.poll() is None

    def exit_code(self) -> int | None:
        """
        Return the exit code if the process has finished, otherwise None.
        """
        if not self.is_running():
            return self._proc.poll() if self._proc else None
        return None

    def pid(self) -> int | None:
        """
        Return the PID of the running process, or None if not running.
        """
        if self.is_running() and self._proc:
            return self._proc.pid
        return None
