import signal
import threading
import time
import types

from server_runner.commandline.commandline import CommandLine
from server_runner.config.logging import get_logger, setup_logging
from server_runner.steam.gsm_setup import create_game_server_manager
from server_runner.utils.system_metrics import (
    SYSTEM_MEMORY_THRESHOLD,
    SystemMetrics,
    get_memory_usage_percent,
)
from server_runner.workflow.workflow_setup import create_workflow_engine

setup_logging()
log = get_logger()


def main():
    command_line = CommandLine()
    config = command_line.parse_server_config()

    gsm = create_game_server_manager(config)
    system = SystemMetrics(SYSTEM_MEMORY_THRESHOLD, get_memory_usage_percent)
    engine = create_workflow_engine(gsm, system)

    stop_event = threading.Event()

    def shutdown_signal_handler(signum: int, _: types.FrameType | None) -> None:
        log.info(f"Received signal {signum}, shutting down...")
        stop_event.set()

    signal.signal(signal.SIGINT, shutdown_signal_handler)
    signal.signal(signal.SIGTERM, shutdown_signal_handler)

    engine.start()
    log.info("Workflow engine started")
    engine.enqueue_job("update_start")

    try:
        while not stop_event.is_set():
            time.sleep(1)
    except Exception:
        log.exception("Error during main loop")
    finally:
        log.info("Stopping server and engine...")
        gsm.stop()
        engine.stop()
        log.info("Shutdown complete")


if __name__ == "__main__":
    log.info("Program started")
    main()
    log.info("Program finished")
