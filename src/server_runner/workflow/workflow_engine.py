import queue
import threading
import time
from collections.abc import Callable
from typing import Literal, TypedDict

import schedule  # type: ignore[reportUnknownMemberType]

from server_runner.config.logging import get_logger
from server_runner.steam.game_server_manager import GameServerManager
from server_runner.workflow.job_definitions import JobDef, JobID
from server_runner.workflow.workflow_catalog import WorkflowCatalog
from server_runner.workflow.workflow_job import WorkflowJob
from server_runner.workflow.workflow_queue import WorkflowQueue

log = get_logger()


class ScheduleEntry(TypedDict):
    times: list[str]
    job_id: str
    condition: Callable[[], bool]
    interval: Literal["minute", "hour", "day"]


class WorkflowEngine:
    """Engine to schedule, enqueue, and execute workflow jobs."""

    def __init__(
        self,
        gsm: GameServerManager,
        catalog: WorkflowCatalog[JobID, WorkflowJob],
    ):
        self.gsm = gsm
        self.catalog = catalog
        self.queue: WorkflowQueue = WorkflowQueue()

        self._stop_event = threading.Event()
        self._sentinel: WorkflowJob = WorkflowJob.sentinel()

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
    def _schedule_job(self, job_id: JobID, schedule_info: JobDef["schedule"]) -> None:
        """Schedule a single job from its job definition if schedule info exists."""
        if not schedule_info:
            return  # no schedule for this job

        times = schedule_info.get("times", [])
        interval = schedule_info.get("interval")
        condition: Callable[[], bool] = schedule_info.get(
            "condition", lambda: True
        )  # default always true

        if not interval or not times:
            return  # invalid schedule

        def conditional_job():
            try:
                if condition():
                    job = self.catalog.get(job_id)
                    if job:
                        self.queue.enqueue(job)
            except Exception as e:
                log.error(f"Error evaluating schedule for job '{job_id}': {e}")

        for t in times:
            if interval == "minute":
                schedule.every().minutes.at(t).do(conditional_job)
            elif interval == "hour":
                schedule.every().hour.at(t).do(conditional_job)
            elif interval == "day":
                schedule.every().day.at(t).do(conditional_job)

    def _setup_schedules(self) -> None:
        """Iterate all job definitions and schedule the ones with schedule info."""
        for job_id, job_def in self.job_defs.items():
            self._schedule_job(job_id, job_def.get("schedule"))

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
                job: WorkflowJob = self.queue.get(
                    timeout=1
                )  # blocks until item or timeout
            except queue.Empty:
                continue  # loop back without busy-waiting

            if job.is_sentinel:
                self.queue.task_done()
                log.debug("Sentinel WorkflowJob found... exiting consumer")
                break

            try:
                log.info(f"Running job: {job}")
                job.run_all()
                log.info(f"Completed job: {job}")
                self.queue.prune_lower_priority(job)
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

    def enqueue_job(self, job_name: str) -> bool:
        """
        Enqueue a job by name.

        Args:
            job_name: The identifier of the job in the catalog.

        Returns:
            True if the job was enqueued successfully, False if not found.
        """
        job = self.catalog.get(job_name)
        if not job:
            log.warning(f"Job '{job_name}' not found in catalog")
            return False

        self.queue.enqueue(job)
        log.info(f"Job '{job_name}' enqueued")
        return True
