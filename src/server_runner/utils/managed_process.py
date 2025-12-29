import os
import signal
import subprocess
from collections.abc import Sequence
from subprocess import PIPE, Popen


class ManagedProcess:
    def __init__(
        self,
        command: Sequence[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        shell: bool = False,
    ):
        # Command to execute (e.g. ["sleep", "10"])
        self.command = command

        # Optional working directory
        self.cwd = cwd

        # Optional environment variables
        self.env = env

        # Whether to execute through the shell
        self.shell = shell

        # Internal handle to the running process.
        # Invariant:
        #   - None  -> process not running
        #   - Popen -> process running
        self._proc: Popen[str] | None = None

    # ---------- lifecycle ----------

    def start(self) -> None:
        """
        Start the process.

        Raises:
            RuntimeError: if the process is already running.
        """
        if self._proc is not None:
            raise RuntimeError("Process already started")

        self._proc = subprocess.Popen(
            self.command,
            cwd=self.cwd,
            env=self.env,
            shell=self.shell,
            stdout=PIPE,
            stderr=PIPE,
            text=True,
            start_new_session=True,  # isolate process group (Linux)
        )

    def terminate(self, timeout: float = 5.0) -> None:
        """
        Gracefully terminate the process using SIGTERM.

        If the process does not exit within `timeout`,
        it will be forcefully killed.
        """
        if self._proc is None:
            return

        self._proc.terminate()
        try:
            self._proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.kill()
        finally:
            self._proc = None

    def kill(self) -> None:
        """
        Forcefully kill the process and its entire process group
        using SIGKILL.
        """
        if self._proc is None:
            return

        os.killpg(self._proc.pid, signal.SIGKILL)
        self._proc.wait()
        self._proc = None

    def restart(self) -> None:
        """
        Restart the process by terminating it (if running)
        and starting it again.
        """
        self.terminate()
        self.start()

    # ---------- inspection ----------

    def is_running(self) -> bool:
        """
        Return True if the process is currently running.
        Handles processes that have exited unexpectedly.
        """
        if self._proc is None:
            return False

        # poll() returns None if still running, or the exit code if finished
        return self._proc.poll() is None

    def exit_code(self) -> int | None:
        """
        Return the exit code if the process has finished, otherwise None.
        """
        if self._proc is None:
            return None
        return self._proc.poll()

    def pid(self) -> int | None:
        """
        Return the PID of the running process, or None if not running.
        """
        return self._proc.pid if self._proc else None
