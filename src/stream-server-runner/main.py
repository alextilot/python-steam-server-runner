import logging
import threading
import time

import schedule
from actions import (
    ActionFreshStart,
    ActionOutOfMemory,
    ActionRestart,
    ActionStart,
    ActionType,
    ActionUpdate,
)
from commandline import CommandLine
from state_checker import StateChecker
from steam.palworld_api import PalWorldAPI
from steam.steam_game import SteamGame
from tasks import TaskFactory, TaskRegistry
from utils.cascading_queue import CascadingQueue
from utils.system import System

# Get the logger you want to disable (e.g., 'schedule' logger)
logger_to_disable = logging.getLogger("schedule")
logger_to_disable.disabled = True

file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Configure logging with basicConfig
logging.basicConfig(
    level=logging.DEBUG,  # Minimum level to log
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(module)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[file_handler, stream_handler],
)

log = logging.getLogger(__name__)


def consumer_thread(queue: CascadingQueue):
    def consumer():
        while True:
            try:
                task = queue.get()
                if task is None:  # Sentinel value
                    queue.task_done()
                    log.debug("Sentinel value found... exiting")
                    break
                log.info(f"running: {task}")
                task.run()
                queue.task_done()
                log.info(f"completed: {task}")
                queue.remove_lower_priority(task)
                time.sleep(1)
            except Exception as e:
                log.error(f"Error during event loop: {e}")

    return consumer


def conditional(condition_func, action_func, *args, **kwargs):
    if condition_func():
        return action_func(*args, **kwargs)
    return None


def producer_thread(queue: CascadingQueue, check: StateChecker, tasks: TaskRegistry):
    schedule.every().minutes.at(":00").do(
        conditional, check.is_game_stopped, queue.enqueue, tasks.get(ActionType.START)
    )

    for minute in [":00", ":10", ":20", ":30", ":40", ":50"]:
        schedule.every().hour.at(minute).do(
            conditional,
            check.has_memory_leak,
            queue.enqueue,
            tasks.get(ActionType.OUT_OF_MEMORY),
        )

    for minute in [":00", ":15", ":30", ":45"]:
        schedule.every().hour.at(minute).do(
            conditional,
            check.is_update_available,
            queue.enqueue,
            tasks.get(ActionType.UPDATE),
        )

    schedule.every().day.at("05:45").do(
        conditional,
        check.is_game_running,
        queue.enqueue,
        tasks.get(ActionType.RESTART),
    )

    def producer():
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                log.error(f"Error during schedule loop: {e}")

    return producer


def main():
    command_line = CommandLine()
    queue = CascadingQueue()

    args = command_line.parse_start_args()

    steamgame = SteamGame(
        args["steam_path"], args["app_id"], args["game_name"], args["game_args"]
    )
    palworld_api = PalWorldAPI(
        args["api"],
        args["username"],
        args["password"],
    )
    system = System()

    checker = StateChecker(palworld_api, steamgame, system)

    task_registery = TaskRegistry()
    task_factory = TaskFactory(task_registery)

    task_factory.create(
        5, ActionType.FRESH_START, ActionFreshStart(palworld_api, steamgame, 0)
    )
    task_factory.create(4, ActionType.START, ActionStart(palworld_api, steamgame, 0))
    task_factory.create(
        3, ActionType.RESTART, ActionRestart(palworld_api, steamgame, 15)
    )
    task_factory.create(
        4, ActionType.OUT_OF_MEMORY, ActionOutOfMemory(palworld_api, steamgame, 5)
    )
    task_factory.create(5, ActionType.UPDATE, ActionUpdate(palworld_api, steamgame, 5))

    event_thread = threading.Thread(
        name="EventThread", target=consumer_thread(queue), daemon=True
    )

    scheduler_thread = threading.Thread(
        name="ScheudlerThread",
        target=producer_thread(queue, checker, task_registery),
        daemon=True,
    )

    log.debug("system data initalized")

    try:
        event_thread.start()
        scheduler_thread.start()
        queue.enqueue(task_registery.get(ActionType.FRESH_START))
        while True:
            time.sleep(1)
            output, err = command_line.parse_command(palworld_api.call)
            if output is not None:
                print(output)
            if err:
                break
    except Exception as e:
        log.error(f"Error parsing command: {e}")
    finally:
        steamgame.stop()
        scheduler_thread.join()
        queue.enqueue(None)
        event_thread.join()


if __name__ == "__main__":
    try:
        log.debug("Main: Program started")
        main()
    except Exception as e:
        log.error(f"Error in main {e}")
    finally:
        log.debug("Main: Program finished")
