import signal
import threading
import types

from server_runner.commandline.commandline import CommandLine
from server_runner.config.logging import get_logger, setup_logging
from server_runner.steam.factory import build_game_server
from server_runner.workflow.job_definitions import JobID
from server_runner.workflow.workflow_builder import create_workflow_engine

setup_logging()
log = get_logger()

shutdown_event = threading.Event()


def shutdown_signal_handler(signum: int, _: types.FrameType | None) -> None:
    log.info(f"Received signal {signum}, Initiating graceful shutdown...")
    shutdown_event.set()


def main():
    # Register the signal handlers.
    signal.signal(signal.SIGTERM, shutdown_signal_handler)
    signal.signal(signal.SIGINT, shutdown_signal_handler)

    command_line = CommandLine()
    config = command_line.parse_server_config()

    server = build_game_server(config)
    engine = create_workflow_engine(server)

    engine.start()
    log.info("Workflow engine started")

    # Enqueue an initial job
    engine.enqueue_job(JobID.UPDATE_START)

    try:
        # Use wait() to respond immediately to shutdown_event
        while not shutdown_event.is_set():
            shutdown_event.wait(timeout=1)
    except Exception:
        log.exception("Error during main loop")
        exit(1)
    finally:
        server.stop()
        engine.stop()
        log.info("Cleanup operations complete. Exiting.")


if __name__ == "__main__":
    log.info("Program started")
    main()
    log.info("Program finished")
