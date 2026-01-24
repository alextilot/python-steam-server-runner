import queue
import threading
import time
from collections.abc import Callable

import schedule  # type: ignore

from server_runner.config.logging import get_logger
from server_runner.steam.managed_game_server import ManagedGameServer
from server_runner.workflow.job_definitions import JobID, JobSchedule
from server_runner.workflow.workflow_job import WorkflowJob

log = get_logger()


class WorkflowEngine:
    """Engine to schedule, enqueue, and execute workflow jobs."""

    def __init__(
        self,
        server: ManagedGameServer,
        jobs: dict[JobID, WorkflowJob],
        schedules: dict[JobID, JobSchedule],
    ):
        self.server = server
        self.jobs = jobs
        self.schedules = schedules
        self.queue: queue.Queue[WorkflowJob] = queue.Queue()

        self._stop_event = threading.Event()
        self._sentinel: WorkflowJob = WorkflowJob.sentinel()

        self._consumer_thread = threading.Thread(
            target=self._consumer, name="ConsumerThread", daemon=True
        )
        self._scheduler_thread = threading.Thread(
            target=self._scheduler, name="SchedulerThread", daemon=True
        )

    # ------------------------
    # Scheduler Helpers
    # ------------------------
    def _schedule_job(self, job_id: JobID, schedule_info: JobSchedule) -> None:
        """Schedule a single job using its schedule info."""
        times = schedule_info.get("times", [])
        interval = schedule_info.get("interval")
        condition: Callable[[], bool] = schedule_info.get("condition", lambda: True)

        if not interval or not times:
            return

        job = self.jobs.get(job_id)
        if not job:
            log.warning(f"Cannot schedule unknown job '{job_id.name}'")
            return

        def conditional_job():
            try:
                if condition():
                    self.queue.put(job)
            except Exception as e:
                log.error(f"Error evaluating schedule for job '{job.name}': {e}")

        for t in times:
            if interval == "minute":
                schedule.every().minutes.at(t).do(conditional_job)
            elif interval == "hour":
                schedule.every().hour.at(t).do(conditional_job)
            elif interval == "day":
                schedule.every().day.at(t).do(conditional_job)

    def _setup_schedules(self):
        for job_id, schedule_info in self.schedules.items():
            self._schedule_job(job_id, schedule_info)

    # ------------------------
    # Scheduler (Producer)
    # ------------------------
    def _scheduler(self):
        self._setup_schedules()
        while not self._stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                log.error(f"Error during schedule loop: {type(e).__name__} - {e}")

    # ------------------------
    # Consumer
    # ------------------------
    def _consumer(self):
        while True:
            try:
                job: WorkflowJob = self.queue.get(timeout=1)
            except queue.Empty:
                continue

            if job.is_sentinel:
                self.queue.task_done()
                log.debug("Sentinel WorkflowJob found... exiting consumer")
                break

            try:
                log.info(f"Running job: {job}")
                job.run_all()
                log.info(f"Completed job: {job}")
            finally:
                self.queue.task_done()

    # ------------------------
    # Public API
    # ------------------------
    def start(self):
        log.debug("Starting WorkflowEngine threads")
        self._consumer_thread.start()
        self._scheduler_thread.start()
        log.debug("WorkflowEngine threads started")

    def stop(self):
        log.debug("Stopping WorkflowEngine")
        self._stop_event.set()
        self.queue.put(self._sentinel)
        self._scheduler_thread.join()
        self._consumer_thread.join()
        log.debug("WorkflowEngine stopped")

    def enqueue_job(self, job_id: JobID) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            log.warning(f"Job '{job_id.name}' not found")
            return False
        self.queue.put(job)
        log.info(f"Job '{job.name}' enqueued")
        return True
