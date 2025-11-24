import threading
import time
from collections.abc import Callable
from typing import Literal, TypedDict

import schedule
from status import Status
from tasks import TaskFactory
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
        status: Status,
        jobs: JobCatalog,
        task_factory: TaskFactory,
    ):
        self.queue: WorkflowQueue = WorkflowQueue()
        self.status: Status = status
        self.jobs: JobCatalog = jobs
        self.task_factory: TaskFactory = task_factory

        # Sentinel WorkflowJob to signal shutdown
        self._sentinel: WorkflowJob = WorkflowJob.sentinel()

        # Threads
        self._consumer_thread = threading.Thread(
            target=self._consumer, name="EventThread", daemon=True
        )
        self._producer_thread = threading.Thread(
            target=self._producer, name="ScheduleThread", daemon=True
        )

    # ------------------------
    # Producer
    # ------------------------
    def _producer(self) -> None:
        """Schedule workflow jobs based on status conditions."""

        def conditional(condition_func: Callable[[], bool], job: WorkflowJob) -> None:
            if condition_func():
                self.queue.enqueue(job)

        # Dynamic scheduling mapping
        schedule_map: list[ScheduleEntry] = [
            # Every minute
            {
                "times": [":00"],
                "job_id": "start",
                "condition": self.status.is_game_stopped,
                "interval": "minute",
            },
            # Every 10 minutes for memory leaks
            {
                "times": [":00", ":10", ":20", ":30", ":40", ":50"],
                "job_id": "oom",
                "condition": self.status.has_memory_leak,
                "interval": "hour",
            },
            # Every 15 minutes for updates
            {
                "times": [":00", ":15", ":30", ":45"],
                "job_id": "update",
                "condition": self.status.is_update_available,
                "interval": "hour",
            },
            # Daily restart
            {
                "times": ["05:45"],
                "job_id": "restart",
                "condition": self.status.is_game_running,
                "interval": "day",
            },
        ]

        # Schedule the jobs
        for entry in schedule_map:
            job = self.jobs.get(entry["job_id"])

            if job is None:
                log.warning(
                    f"Workflow job '{entry['job_id']}' not found; skipping scheduling."
                )
                continue  # skip missing jobs entirely

            for t in entry["times"]:
                if entry["interval"] == "minute":
                    schedule.every().minutes.at(t).do(
                        conditional, entry["condition"], job
                    )
                elif entry["interval"] == "hour":
                    schedule.every().hour.at(t).do(conditional, entry["condition"], job)
                elif entry["interval"] == "day":
                    schedule.every().day.at(t).do(conditional, entry["condition"], job)

        # Schedule loop
        while True:
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
                item: WorkflowJob = self.queue.get()

                if item.is_sentinel:
                    self.queue.task_done()
                    log.debug("Sentinel WorkflowJob found... exiting consumer")
                    break

                log.info(f"running: {item}")
                item.run_all()
                self.queue.task_done()
                log.info(f"completed: {item}")
                self.queue.prune_lower_priority(item)

            except Exception as e:
                log.error(f"Error during consumer loop: {type(e).__name__} - {e}")

            time.sleep(1)  # always sleep to prevent busy loop

    # ------------------------
    # Public API
    # ------------------------
    def start(self) -> None:
        """Start the producer and consumer threads."""
        log.debug("Starting WorkflowEngine threads")
        self._consumer_thread.start()
        self._producer_thread.start()
        log.debug("WorkflowEngine threads started")

    def stop(self) -> None:
        """Stop the engine by sending a sentinel and joining threads."""
        log.debug("Stopping WorkflowEngine")
        self.queue.enqueue(self._sentinel)  # sentinel to stop consumer
        self._producer_thread.join()
        self._consumer_thread.join()
        log.debug("WorkflowEngine stopped")
