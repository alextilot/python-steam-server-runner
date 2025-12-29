import queue
import threading
import time
from collections.abc import Callable
from typing import Literal, TypedDict

import schedule
from status_manager import StatusManager
from workflow.workflow_catalog import WorkflowCatalog
from workflow.workflow_job import WorkflowJob
from workflow.workflow_queue import WorkflowQueue

from server_runner.config.logging import get_logger

log = get_logger()


class ScheduleEntry(TypedDict):
    times: list[str]
    job_id: str
    condition: Callable[[], bool]
    interval: Literal["minute", "hour", "day"]


# Reusable type alias
JobCatalog = WorkflowCatalog[str, WorkflowJob]


class WorkflowEngine:
    """Engine to schedule, enqueue, and execute workflow jobs."""

    def __init__(
        self,
        status: StatusManager,
        jobs: JobCatalog,
    ):
        self.status = status
        self.jobs = jobs
        self.queue: WorkflowQueue = WorkflowQueue()

        # Sentinel WorkflowJob to signal shutdown
        self._sentinel: WorkflowJob = WorkflowJob.sentinel()

        self._stop_event = threading.Event()

        # Threads
        self._consumer_thread = threading.Thread(
            target=self._consumer, name="ConsumerThread", daemon=True
        )
        self._scheduler_thread = threading.Thread(
            target=self._scheduler, name="SchedulerThread", daemon=True
        )

    # ------------------------
    # Scheduler Helpers
    # ------------------------
    def _get_schedule_map(self) -> list[ScheduleEntry]:
        """Return the schedule configuration."""
        return [
            {
                "times": [":00"],
                "job_id": "start",
                "condition": self.status.is_game_stopped,
                "interval": "minute",
            },
            {
                "times": [":00", ":10", ":20", ":30", ":40", ":50"],
                "job_id": "oom",
                "condition": self.status.has_memory_leak,
                "interval": "hour",
            },
            {
                "times": [":00", ":15", ":30", ":45"],
                "job_id": "update",
                "condition": self.status.is_update_available,
                "interval": "hour",
            },
            {
                "times": ["05:45"],
                "job_id": "restart",
                "condition": self.status.is_game_running,
                "interval": "day",
            },
        ]

    def _schedule_job(self, entry: ScheduleEntry) -> None:
        """Schedule a single job based on its entry and interval."""

        def conditional_job():
            try:
                if entry["condition"]():
                    job = self.jobs.get(entry["job_id"])
                    if job:
                        self.queue.enqueue(job)
            except Exception as e:
                log.error(
                    f"Error evaluating condition for job '{entry['job_id']}': {e}"
                )

        for t in entry["times"]:
            if entry["interval"] == "minute":
                schedule.every().minutes.at(t).do(conditional_job)
            elif entry["interval"] == "hour":
                schedule.every().hour.at(t).do(conditional_job)
            elif entry["interval"] == "day":
                schedule.every().day.at(t).do(conditional_job)

    # ------------------------
    # Scheduler (Producer)
    # ------------------------
    def _scheduler(self) -> None:
        """Continuously run scheduled jobs while engine is active."""
        for entry in self._get_schedule_map():
            self._schedule_job(entry)

        while not self._stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                log.error(f"Error during schedule loop: {type(e).__name__} - {e}")

    # ------------------------
    # Consumer
    # ------------------------
    def _consumer(self) -> None:
        """Consume workflow jobs from the queue and execute them."""
        while True:
            try:
                item: WorkflowJob = self.queue.get(
                    timeout=1
                )  # blocks until item or timeout
            except queue.Empty:
                continue  # loop back without busy-waiting

            if item.is_sentinel:
                self.queue.task_done()
                log.debug("Sentinel WorkflowJob found... exiting consumer")
                break

            try:
                log.info(f"Running: {item}")
                item.run_all()
                log.info(f"Completed: {item}")
                self.queue.prune_lower_priority(item)
            finally:
                self.queue.task_done()

    # ------------------------
    # Public API
    # ------------------------
    def start(self) -> None:
        """Start the scheduler and consumer threads."""
        log.debug("Starting WorkflowEngine threads")
        self._consumer_thread.start()
        self._scheduler_thread.start()
        log.debug("WorkflowEngine threads started")

    def stop(self) -> None:
        """Stop the engine by signaling threads and joining them."""
        log.debug("Stopping WorkflowEngine")
        self._stop_event.set()  # stop scheduler
        self.queue.enqueue(self._sentinel)  # stop consumer
        self._scheduler_thread.join()
        self._consumer_thread.join()
        log.debug("WorkflowEngine stopped")
