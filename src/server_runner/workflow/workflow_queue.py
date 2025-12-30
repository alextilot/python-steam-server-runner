from queue import Empty, PriorityQueue

from server_runner.config.logging import get_logger
from server_runner.workflow.workflow_job import WorkflowJob

log = get_logger()


class WorkflowQueue(PriorityQueue[WorkflowJob]):
    """A priority-based workflow queue for WorkflowItems."""

    def __str__(self) -> str:
        items = list(self.queue)
        string_items = [str(item) for item in items]
        return f"Queue ({len(items)}) Contents: {' | '.join(string_items)}"

    # ------------------------
    # Internal Helpers
    # ------------------------

    def _clear(self) -> None:
        """Remove all non-sentinel items from the queue."""
        temp: list[WorkflowJob] = []
        while not self.empty():
            try:
                item = self.get_nowait()
                self.task_done()
                if item.is_sentinel:
                    temp.append(item)  # Keep sentinel if already in queue
            except Empty:
                break
        for item in temp:
            self.put(item)
        log.info("Queue emptied")

    # ------------------------
    # Public API
    # ------------------------

    def enqueue(self, item: WorkflowJob) -> None:
        """Add a WorkflowItem. If sentinel, clear the queue first."""
        if item.is_sentinel:
            log.info("Enqueue sentinel -> clearing queue")
            self._clear()
            self.put(item)
            return

        log.info(f"enqueue: {item}")
        self.put(item)

    def prune_lower_priority(self, base: WorkflowJob) -> None:
        """
        Remove all items with priority numerically greater than base.priority.
        (Higher numeric value = lower actual priority.)
        """
        temp_queue: PriorityQueue[WorkflowJob] = PriorityQueue()

        while not self.empty():
            try:
                item = self.get_nowait()
                self.task_done()
            except Empty:
                break

            if item.is_sentinel or item.priority <= base.priority:
                temp_queue.put(item)
            else:
                log.info(f"dequeue: {item}")

        # Restore surviving items
        while not temp_queue.empty():
            self.put(temp_queue.get())

    def peek(self) -> WorkflowJob | None:
        """Return the next item without removing it, or None if empty."""
        try:
            # PriorityQueue keeps heap in `queue` attribute
            return self.queue[0]
        except IndexError:
            return None
