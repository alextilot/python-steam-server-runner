import time
from collections.abc import Generator
from typing import IO

import pytest

from server_runner.utils.managed_process import ManagedProcess
from tests.integration.helpers import (
    crashing_python_process,
    long_running_python_process,
    parent_with_child_process,
    process_exists,
    stdout_stderr_emitter,
    wait_for_child_process,
)


@pytest.fixture
def proc() -> Generator[ManagedProcess]:
    """
    Provides a clean ManagedProcess instance and guarantees cleanup,
    even if a test fails mid-execution.
    """
    mp = ManagedProcess(long_running_python_process())
    yield mp
    mp.kill()


# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------


def test_start_starts_process(proc: ManagedProcess) -> None:
    """
    Verifies that start():
    - launches a real OS process
    - exposes a valid PID
    - reports running state correctly
    """
    proc.start()

    assert proc.is_running()

    pid = proc.pid()
    assert pid is not None
    assert process_exists(pid)


def test_terminate_gracefully_stops_process(proc: ManagedProcess) -> None:
    """
    Verifies that terminate():
    - sends SIGTERM to the process group
    - allows clean shutdown
    - releases OS resources
    """
    proc.start()
    pid = proc.pid()
    assert pid is not None

    proc.terminate()

    assert not proc.is_running()
    # When OS SEGTERMS a process it is negative 15
    assert proc.exit_code() == -15
    assert not process_exists(pid)


def test_kill_terminates_children() -> None:
    """
    Verifies that kill():
    - forcibly kills the parent process
    - recursively kills child processes
    - leaves no orphaned processes behind

    This protects against zombie servers and leaked subprocess trees.
    """
    proc = ManagedProcess(parent_with_child_process())
    proc.start()

    pid = proc.pid()
    assert pid is not None

    children = wait_for_child_process(pid, timeout=2.0)
    assert children, "Expected child processes to exist"

    proc.kill()

    assert not process_exists(pid)
    for child in children:
        assert not process_exists(child.pid)


def test_restart_creates_new_pid(proc: ManagedProcess) -> None:
    """
    Verifies that restart():
    - shuts down the existing process
    - starts a fresh process instance
    - does not reuse the same PID
    """
    proc.start()
    first_pid = proc.pid()
    assert first_pid is not None

    proc.restart()

    second_pid = proc.pid()
    assert second_pid is not None

    assert first_pid != second_pid
    assert not process_exists(first_pid)
    assert process_exists(second_pid)


def test_unexpected_exit_is_detected() -> None:
    """
    Verifies that ManagedProcess detects unexpected crashes
    and exposes the correct exit code.
    """
    proc = ManagedProcess(crashing_python_process(42))
    proc.start()

    time.sleep(0.2)

    assert not proc.is_running()
    assert proc.exit_code() == 42


# ---------------------------------------------------------------------------
# I/O stream tests
# ---------------------------------------------------------------------------


def test_stdout_and_stderr_are_readable() -> None:
    """
    Verifies that:
    - stdout is captured
    - stderr is captured
    - text mode decoding works
    """
    proc = ManagedProcess(stdout_stderr_emitter())
    proc.start()

    stdout: IO[str] | None = proc.stdout()
    stderr: IO[str] | None = proc.stderr()

    assert stdout is not None
    assert stderr is not None

    assert stdout.readline().strip() == "hello stdout"
    assert stderr.readline().strip() == "hello stderr"

    proc.kill()


def test_output_arrives_before_termination() -> None:
    """
    Verifies that output is flushed and readable
    before the process is terminated.
    """
    proc = ManagedProcess(stdout_stderr_emitter())
    proc.start()

    stdout: IO[str] | None = proc.stdout()
    assert stdout is not None

    line = stdout.readline().strip()
    assert line == "hello stdout"

    proc.terminate()
    assert not proc.is_running()


def test_pipes_close_after_kill() -> None:
    """
    Verifies that stdout/stderr pipes are closed
    after the process is killed, preventing FD leaks.
    """
    proc = ManagedProcess(stdout_stderr_emitter())
    proc.start()

    stdout: IO[str] | None = proc.stdout()
    stderr: IO[str] | None = proc.stderr()
    assert stdout is not None
    assert stderr is not None

    proc.kill()

    # Once killed, the pipes should be closed or EOF
    assert stdout.closed or stdout.read() == ""
    assert stderr.closed or stderr.read() == ""
