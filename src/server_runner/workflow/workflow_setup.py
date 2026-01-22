from server_runner.steam.game_server_manager import GameServerManager
from server_runner.workflow.job_definitions import get_job_definitions
from server_runner.workflow.job_ids import JobID
from server_runner.workflow.workflow_catalog import WorkflowCatalog
from server_runner.workflow.workflow_engine import WorkflowEngine
from server_runner.workflow.workflow_job import WorkflowJob


def build_catalog(gsm: GameServerManager) -> WorkflowCatalog[JobID, WorkflowJob]:
    job_defs = get_job_definitions(gsm)
    catalog = WorkflowCatalog[JobID, WorkflowJob]()

    for job_id, data in job_defs.items():
        job = WorkflowJob(name=job_id.name, priority=data["priority"])
        for builder in data["tasks"]:
            job.add_task(builder())
        catalog.register(job_id, job)

    return catalog


# ------------------------
# Engine creator
# ------------------------
def create_workflow_engine(gsm: GameServerManager) -> WorkflowEngine:
    """Convenience function to build jobs and initialize the WorkflowEngine."""
    catalog = build_catalog(gsm)
    engine = WorkflowEngine(gsm, catalog)
    return engine
