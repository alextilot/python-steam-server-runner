import time

from server_runner.commandline.commandline import CommandLine
from server_runner.config.logging import get_logger, setup_logging
from server_runner.status_manager import StatusManager
from server_runner.steam.create_game_api import create_game_api
from server_runner.steam.game_server_manager import GameServerManager
from server_runner.steam.server.controller import SteamServerController
from server_runner.steam.server.install_resolver import SteamInstallResolver
from server_runner.utils.system_metrics import (
    SYSTEM_MEMORY_THRESHOLD,
    SystemMetrics,
    get_memory_usage_percent,
)
from server_runner.workflow.tasks import TaskFactory
from server_runner.workflow.workflow_catalog import WorkflowCatalog
from server_runner.workflow.workflow_engine import WorkflowEngine
from server_runner.workflow.workflow_factories import (
    fresh_start,
    game_restart,
    game_start,
    game_stop,
    game_update,
    out_of_memory,
)
from server_runner.workflow.workflow_job import WorkflowJob

setup_logging()
log = get_logger()


def main():
    command_line = CommandLine()
    config = command_line.parse_server_config()

    resolver = SteamInstallResolver(
        config.app_id, steam_path=config.steam_path, install_dir=config.install_dir
    )

    controller = SteamServerController(
        config.app_id,
        resolver,
        config.game_args,
    )

    api = create_game_api(
        app_id=config.app_id, base_url=config.api_base_url, auth_info=config.auth_info
    )

    gsm = GameServerManager(controller, api)

    tasks = TaskFactory(gsm)

    # Workflow jobs
    jobs = WorkflowCatalog[str, WorkflowJob]()
    jobs.register("fresh", fresh_start(tasks))
    jobs.register("start", game_start(tasks))
    jobs.register("restart", game_restart(tasks))
    jobs.register("oom", out_of_memory(tasks))
    jobs.register("update", game_update(tasks))
    jobs.register("stop", game_stop(tasks))

    # Create the engine
    system_metrics = SystemMetrics(SYSTEM_MEMORY_THRESHOLD, get_memory_usage_percent)
    status_manager = StatusManager(gsm, system_metrics)
    engine = WorkflowEngine(status_manager, jobs)

    # Start scheduling and processing
    engine.start()

    log.debug("system initalized")

    try:
        while True:
            time.sleep(1)
    except Exception as e:
        log.error(f"Error parsing command: {e}")
    finally:
        gsm.stop()
        engine.stop()


if __name__ == "__main__":
    try:
        log.debug("Program started")
        main()
    except Exception as e:
        log.error(f"Error {e}")
    finally:
        log.debug("Program finished")
