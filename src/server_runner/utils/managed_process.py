import os
import subprocess
import sys
from collections.abc import Sequence
from subprocess import Popen

import psutil


class ManagedProcess:
    def __init__(
        self,
        command: Sequence[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        shell: bool = False,
    ):
        self.command = command
        self.cwd = cwd
        self.env = env
        self.shell = shell
        self._proc: Popen | None = None

    # ---------- lifecycle ----------

    def start(self) -> None:
        """
        Start the process, streaming output to the terminal.
        """
        if self._proc is not None:
            raise RuntimeError("Process already started")

        self._proc = subprocess.Popen(
            self.command,
            cwd=self.cwd,
            env=self.env,
            shell=self.shell,
            stdin=sys.stdin,  # allow interactive input
            stdout=sys.stdout,  # live output
            stderr=sys.stderr,  # live error output
            preexec_fn=os.setsid,  # start new session/process group
        )

    def terminate(self, timeout: float = 5.0) -> None:
        """
        Gracefully terminate the process using SIGTERM.
        Falls back to kill() if timeout expires.
        """
        if self._proc is None:
            return

        try:
            self._proc.terminate()
            self._proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.kill()
        finally:
            self._proc = None

    def kill(self) -> None:
        """
        Kill the process and all child processes using psutil.
        """
        if self._proc is None:
            return

        try:
            parent = psutil.Process(self._proc.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except psutil.NoSuchProcess:
            pass
        finally:
            self._proc = None

    def restart(self) -> None:
        """
        Restart the process by terminating and starting it again.
        """
        self.terminate()
        self.start()

    # ---------- inspection ----------

    def is_running(self) -> bool:
        if self._proc is None:
            return False
        return self._proc.poll() is None

    def exit_code(self) -> int | None:
        if self._proc is None:
            return None
        return self._proc.poll()

    def pid(self) -> int | None:
        return self._proc.pid if self._proc else None
