import time

import pytest

from server_runner.utils.managed_process import ManagedProcess
from tests.integration.helpers import sleep_cmd

pytestmark = pytest.mark.integration


def test_process_runs_and_exits_cleanly():
    proc = ManagedProcess(sleep_cmd(0.2))

    proc.start()
    assert proc.is_running()

    # Wait for natural exit
    time.sleep(0.3)

    assert not proc.is_running()
    assert proc.exit_code() == 0
