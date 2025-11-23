import logging
from typing import List

from tasks import Task

log = logging.getLogger(__name__)


class Job:
    def __init__(self, priority: int, name: str):
        self.priority = priority
        self.name = name
        self.tasks: List[Task] = []
        self.working = False

    def __str__(self):
        return f"Job {self.name}, priority: {self.priority}"

    def add(self, task: Task):
        self.tasks.append(task)

    def run(self):
        self.working = True
        for task in self.tasks:
            task.do()
        self.working = False


class JobRegistry:
    def __init__(self):
        self.registry = {}

    def register(self, job_id, job_function):
        self.registry[job_id] = job_function

    def get(self, job_id):
        return self.registry.get(job_id)
