from typing import List

from tasks import Task


class Job:
    def __init__(self, priority: int, name: str, tasks: List[Task] = []):
        self.priority = priority
        self.name = name
        self.tasks = tasks
        self.working = False

    def __str__(self):
        return f"Job {self.name}, priority: {self.priority}"

    def __lt__(self, other):
        if isinstance(other, Job):
            return self.priority < other.priority
        return False

    def __le__(self, other):
        if isinstance(other, Job):
            return self.priority <= other.priority
        return False

    def __gt__(self, other):
        if isinstance(other, Job):
            return self.priority > other.priority
        return False

    def __ge__(self, other):
        if isinstance(other, Job):
            return self.priority >= other.priority
        return False

    def __eq__(self, other):
        if isinstance(other, Job):
            return self.priority == other.priority
        return False

    def __ne__(self, other):
        if isinstance(other, Job):
            return not (self.priority == other.priority)
        return False

    def add(self, task: Task):
        self.tasks.append(task)

    def run(self):
        self.working = True
        for task in self.tasks:
            task.run()
        self.working = False


class JobRegistry:
    def __init__(self):
        self.registry = {}

    def register(self, job_id, job_function):
        self.registry[job_id] = job_function

    def get(self, job_id):
        return self.registry.get(job_id)
