import logging

from actions import Action

log = logging.getLogger(__name__)


class Task:
    def __init__(self, priority: int, name: str, action: Action):
        self.priority = priority
        self.name = name
        self.action = action

    def __str__(self):
        return f"Task {self.name}, priority: {self.priority}"

    def __lt__(self, other):
        if isinstance(other, Task):
            return self.priority < other.priority
        return False

    def __le__(self, other):
        if isinstance(other, Task):
            return self.priority <= other.priority
        return False

    def __gt__(self, other):
        if isinstance(other, Task):
            return self.priority > other.priority
        return False

    def __ge__(self, other):
        if isinstance(other, Task):
            return self.priority >= other.priority
        return False

    def __eq__(self, other):
        if isinstance(other, Task):
            return self.priority == other.priority
        return False

    def __ne__(self, other):
        if isinstance(other, Task):
            return not (self.priority == other.priority)
        return False

    def run(self):
        self.action.execute()


class TaskRegistry:
    def __init__(self):
        self._registry = {}

    def register(self, name: str, task: Task):
        self._registry[name] = task

    def get(self, name: str):
        return self._registry.get(name)


class TaskFactory:
    def __init__(self, registry: TaskRegistry):
        self.registry = registry

    def create(self, priority: int, name: str, action: Action):
        task = Task(priority, name, action)
        log.debug(f"creating: {task}")
        self.registry.register(task.name, task)
        return task
