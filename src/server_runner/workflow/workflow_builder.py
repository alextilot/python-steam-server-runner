from server_runner.steam.managed_game_server import ManagedGameServer
from server_runner.workflow.job_definitions import (
    JobID,
    JobSchedule,
    get_job_definitions,
)
from server_runner.workflow.workflow_engine import WorkflowEngine
from server_runner.workflow.workflow_job import WorkflowJob


def build_jobs_and_schedules(
    server: ManagedGameServer,
) -> tuple[dict[JobID, WorkflowJob], dict[JobID, JobSchedule]]:
    """
    Build WorkflowJob instances and separate schedules.

    Returns:
        jobs: Dict of JobID -> WorkflowJob
        schedules: Dict of JobID -> JobSchedule
    """
    job_defs = get_job_definitions(server)
    jobs: dict[JobID, WorkflowJob] = {}
    schedules: dict[JobID, JobSchedule] = {}

    for job_id, data in job_defs.items():
        # Build job with tasks
        job = WorkflowJob(name=job_id.name, priority=data["priority"])
        for builder in data["tasks"]:
            job.add_task(builder())

        jobs[job_id] = job

        # Separate schedule info
        schedule_info: JobSchedule | None = data.get("schedule")
        if schedule_info is not None:
            schedules[job_id] = schedule_info

    return jobs, schedules


def create_workflow_engine(server: ManagedGameServer) -> WorkflowEngine:
    jobs, schedules = build_jobs_and_schedules(server)
    return WorkflowEngine(server, jobs, schedules)
