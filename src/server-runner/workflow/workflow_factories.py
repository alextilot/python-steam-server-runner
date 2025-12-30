from server_runner.workflow.tasks import TaskFactory
from server_runner.workflow.workflow_job import WorkflowJob


def fresh_start(task: TaskFactory) -> WorkflowJob:
    job = WorkflowJob(priority=1, name="Fresh start")
    job.add_task(task.restart_with_update())
    return job


def game_start(task: TaskFactory) -> WorkflowJob:
    job = WorkflowJob(priority=2, name="Game start")
    job.add_task(task.start())
    return job


def game_restart(task: TaskFactory) -> WorkflowJob:
    job = WorkflowJob(priority=3, name="Game restart")
    job.add_task(task.countdown(job.name, 15))
    job.add_task(task.stop())
    job.add_task(task.start())
    return job


def out_of_memory(task: TaskFactory) -> WorkflowJob:
    job = WorkflowJob(priority=4, name="System out of memory")
    job.add_task(task.countdown(job.name, 5))
    job.add_task(task.stop())
    job.add_task(task.start())
    return job


def game_update(task: TaskFactory) -> WorkflowJob:
    job = WorkflowJob(priority=5, name="Game update")
    job.add_task(task.countdown(job.name, 15))
    job.add_task(task.stop())
    job.add_task(task.restart_with_update())
    return job


def game_stop(task: TaskFactory) -> WorkflowJob:
    job = WorkflowJob(priority=6, name="Game stop")
    job.add_task(task.stop())
    return job
