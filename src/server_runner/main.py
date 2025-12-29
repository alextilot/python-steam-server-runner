import time

from commandline.commandline import CommandLine
from servers.api.games.palworld_api import PalWorldAPI
from servers.game_server_manager import GameServerManager
from servers.steam.steam_game_controller import SteamGameController
from status_manager import StatusManager
from utils.system_metrics import (
    SYSTEM_MEMORY_THRESHOLD,
    SystemMetrics,
    get_memory_usage_percent,
)
from workflow.tasks import TaskFactory
from workflow.workflow_catalog import WorkflowCatalog
from workflow.workflow_engine import WorkflowEngine
from workflow.workflow_factories import (
    fresh_start,
    game_restart,
    game_start,
    game_stop,
    game_update,
    out_of_memory,
)
from workflow.workflow_job import WorkflowJob

from server_runner.config.logging import get_logger, setup_logging
from server_runner.servers.create_game_api import create_game_api

setup_logging()
log = get_logger()


def main():
    command_line = CommandLine()
    config = command_line.parse_server_config()

    controller = SteamGameController(
        config.steam_path,
        config.app_id,
        config.game_name,
        config.game_args,
    )

    api = create_game_api(
        app_id=config.app_id,
        base_url=config.api_base_url,
        username=config.username,
        password=config.password,
    )

    gsm = GameServerManager(api, controller)

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
