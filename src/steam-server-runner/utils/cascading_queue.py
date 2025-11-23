import logging
from queue import PriorityQueue
from typing import Optional

from jobs import Job

log = logging.getLogger(__name__)


class CascadingQueue(PriorityQueue[Optional[Job]]):
    def __init__(self):
        super().__init__()

    def __str__(self):
        items = list(self.queue)
        string_items = [str(item) for item in items]
        return f"Queue ({len(items)}) Contents: {"| ".join(string_items)}"

    def _clear(self):
        while not self.empty():
            self.get()
            self.task_done()
        log.info("emptied")

    def enqueue(self, item: Optional[Job]):
        log.info(f"enqueue: {item}")
        if item is None:  # Sentinel value
            self._clear()
        self.put(item)

    def remove_lower_priority(self, base: Optional[Job]):
        if base is None:
            return
        temp_pq = PriorityQueue()
        while not self.empty():
            item = self.get()
            if item is None:  # Sentinel value
                self.task_done()
                self._clear()
                self.put(None)
                return
            if item.priority <= base.priority:
                temp_pq.put(item)
            else:
                self.task_done()
                log.info(f"dequeue: {item}")
        while not temp_pq.empty():
            self.put(temp_pq.get())
