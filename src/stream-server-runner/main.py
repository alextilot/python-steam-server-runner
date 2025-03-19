import logging
import threading
import time

import schedule
from commandline import CommandLine
from jobs import Job
from server_action import ServerAction
from state_checker import StateChecker
from steam.palworld_api import PalWorldAPI
from steam.steam_game import SteamGame
from tasks import TaskFactory
from utils.cascading_queue import CascadingQueue
from utils.system import SYSTEM_MEMORY_THRESHOLD, System, get_memory_usage_percent

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


def producer_thread():
    def producer():
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                log.error(f"Error during schedule loop: {e}")

    return producer


def consumer_thread(queue: CascadingQueue):
    def consumer():
        while True:
            try:
                item = queue.get()
                if item is None:  # Sentinel value
                    queue.task_done()
                    log.debug("Sentinel value found... exiting")
                    break
                log.info(f"running: {item}")
                item.run()
                queue.task_done()
                log.info(f"completed: {item}")
                queue.remove_lower_priority(item)
                time.sleep(1)
            except Exception as e:
                log.error(f"Error during event loop: {e}")

    return consumer


def conditional(condition_func, action_func, *args, **kwargs):
    if condition_func():
        return action_func(*args, **kwargs)
    return None


def main():
    command_line = CommandLine()
    queue = CascadingQueue()

    args = command_line.parse_start_args()

    system = System(SYSTEM_MEMORY_THRESHOLD, get_memory_usage_percent)

    steamgame = SteamGame(
        args["steam_path"], args["app_id"], args["game_name"], args["game_args"]
    )
    palworld_api = PalWorldAPI(
        args["api"],
        args["username"],
        args["password"],
    )

    checker = StateChecker(palworld_api, steamgame, system)

    action = ServerAction(palworld_api, steamgame)
    task = TaskFactory(action)

    job_fresh_start = Job(1, "Fresh start")
    job_fresh_start.add(task.update())
    job_fresh_start.add(task.start())

    job_start = Job(2, "Game start")
    job_start.add(task.start())

    job_restart = Job(3, "Game restart")
    job_restart.add(task.countdown(job_restart.name, 15))
    job_restart.add(task.stop())
    job_restart.add(task.start())

    job_out_of_memory = Job(4, "System out of memory")
    job_out_of_memory.add(task.countdown(job_out_of_memory.name, 5))
    job_out_of_memory.add(task.stop())
    job_out_of_memory.add(task.start())

    job_update = Job(5, "Game update")
    job_update.add(task.countdown(job_update.name, 15))
    job_update.add(task.stop())
    job_update.add(task.update())
    job_update.add(task.start())

    job_stop = Job(6, "Game stop")
    job_stop.add(task.stop())

    schedule.every().minutes.at(":00").do(
        conditional, checker.is_game_stopped, queue.enqueue, job_start
    )

    for minute in [":00", ":10", ":20", ":30", ":40", ":50"]:
        schedule.every().hour.at(minute).do(
            conditional, checker.has_memory_leak, queue.enqueue, job_out_of_memory
        )

    for minute in [":00", ":15", ":30", ":45"]:
        schedule.every().hour.at(minute).do(
            conditional, checker.is_update_available, queue.enqueue, job_update
        )

    schedule.every().day.at("05:45").do(
        conditional, checker.is_game_running, queue.enqueue, job_restart
    )

    event_thread = threading.Thread(
        name="EventThread", target=consumer_thread(queue), daemon=True
    )

    schedule_thread = threading.Thread(
        name="ScheudleThread",
        target=producer_thread(),
        daemon=True,
    )

    log.debug("system data initalized")

    try:
        event_thread.start()
        schedule_thread.start()
        queue.enqueue(job_fresh_start)
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
        schedule_thread.join()
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
