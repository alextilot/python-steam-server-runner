import logging
import os
import threading
import time
from logging.handlers import TimedRotatingFileHandler

import schedule
from commandline import CommandLine
from jobs import Job, JobRegistry
from server_action import ServerAction
from status import Status
from steam.palworld_api import PalWorldAPI
from steam.steam_game import SteamGame
from tasks import TaskFactory
from utils.cascading_queue import CascadingQueue
from utils.system import SYSTEM_MEMORY_THRESHOLD, System, get_memory_usage_percent

log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file_path = os.path.join(log_dir, "app.log")

# Get the logger you want to disable (e.g., 'schedule' logger)
logger_to_disable = logging.getLogger("schedule")
logger_to_disable.disabled = True

# file_handler = logging.FileHandler("app.log")
file_handler = TimedRotatingFileHandler(
    log_file_path, when="midnight", interval=1, backupCount=7
)
file_handler.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)

# Configure logging with basicConfig
logging.basicConfig(
    level=logging.DEBUG,  # Minimum level to log
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(module)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[file_handler, stream_handler],
)

log = logging.getLogger(__name__)


def conditional(condition_func, action_func, *args, **kwargs):
    if condition_func():
        return action_func(*args, **kwargs)
    return None


def producer_thread(queue: CascadingQueue, status: Status, jobs: JobRegistry):
    def producer():
        schedule.every().minutes.at(":00").do(
            conditional, status.is_game_stopped, queue.enqueue, jobs.get("start")
        )

        for minute in [":00", ":10", ":20", ":30", ":40", ":50"]:
            schedule.every().hour.at(minute).do(
                conditional, status.has_memory_leak, queue.enqueue, jobs.get("oom")
            )

        for minute in [":00", ":15", ":30", ":45"]:
            schedule.every().hour.at(minute).do(
                conditional,
                status.is_update_available,
                queue.enqueue,
                jobs.get("update"),
            )

        schedule.every().day.at("05:45").do(
            conditional, status.is_game_running, queue.enqueue, jobs.get("restart")
        )

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
                print(queue)
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

    status = Status(palworld_api, steamgame, system)

    action = ServerAction(palworld_api, steamgame)
    task = TaskFactory(action)

    jobs = JobRegistry()

    job_fresh_start = Job(1, "Fresh start")
    job_fresh_start.add(task.update())
    job_fresh_start.add(task.start())
    jobs.register("fresh", job_fresh_start)

    job_start = Job(2, "Game start")
    job_start.add(task.start())
    jobs.register("start", job_start)

    job_restart = Job(3, "Game restart")
    job_restart.add(task.countdown(job_restart.name, 15))
    job_restart.add(task.stop())
    job_restart.add(task.start())
    jobs.register("restart", job_restart)

    job_out_of_memory = Job(4, "System out of memory")
    job_out_of_memory.add(task.countdown(job_out_of_memory.name, 5))
    job_out_of_memory.add(task.stop())
    job_out_of_memory.add(task.start())
    jobs.register("oom", job_out_of_memory)

    job_update = Job(5, "Game update")
    job_update.add(task.countdown(job_update.name, 15))
    job_update.add(task.stop())
    job_update.add(task.update())
    job_update.add(task.start())
    jobs.register("update", job_update)

    job_stop = Job(6, "Game stop")
    job_stop.add(task.stop())
    jobs.register("stop", job_stop)

    event_thread = threading.Thread(
        name="EventThread", target=consumer_thread(queue), daemon=True
    )

    schedule_thread = threading.Thread(
        name="ScheudleThread",
        target=producer_thread(queue, status, jobs),
        daemon=True,
    )

    log.debug("system data initalized")

    try:
        queue.enqueue(job_fresh_start)
        event_thread.start()
        schedule_thread.start()
        while True:
            time.sleep(1)
            # output, err = command_line.parse_command(palworld_api.call)
            # if output is not None:
            #     print(output)
            # if err:
            #     break
    except Exception as e:
        log.error(f"Error parsing command: {e}")
    finally:
        steamgame.stop()
        schedule_thread.join()
        queue.enqueue(None)
        event_thread.join()


if __name__ == "__main__":
    try:
        log.debug("Program started")
        main()
    except Exception as e:
        log.error(f"Error {e}")
    finally:
        log.debug("Program finished")
