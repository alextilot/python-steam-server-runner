from dataclasses import dataclass, field

from tasks import Task

from server_runner.config.logging import get_logger

log = get_logger()

MAX_INT = 2_147_483_648


@dataclass(order=True)
class WorkflowJob:
    """A single workflow containing a prioritized list of tasks."""

    priority: int
    name: str
    _tasks: list[Task] = field(default_factory=list, compare=False)
    _working: bool = field(default=False, compare=False)
    is_sentinel: bool = field(default=False, compare=False)

    @classmethod
    def sentinel(cls) -> "WorkflowJob":
        """Create a sentinel workflow item."""
        return cls(priority=MAX_INT, name="SENTINEL", is_sentinel=True)

    def __str__(self):
        return f"WorkflowJob(name={self.name}, priority={self.priority})"

    @property
    def tasks(self) -> list[Task]:
        """Return tasks in order. Read-only from outside."""
        return list(self._tasks)

    @property
    def is_working(self) -> bool:
        return self._working

    def add_task(self, task: Task):
        """Append a task to this workflow."""
        self._tasks.append(task)

    def run_all(self):
        """Execute all tasks in sequence."""
        self._working = True
        try:
            for task in self._tasks:
                task.do()
        finally:
            self._working = False
