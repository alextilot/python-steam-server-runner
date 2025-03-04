import logging
from queue import PriorityQueue
from typing import Optional, TypeVar

log = logging.getLogger(__name__)

T = TypeVar("T")
QueueItem = Optional[T]


class CascadingQueue(PriorityQueue[QueueItem]):
    def __init__(self):
        super().__init__()

    def _clear(self):
        while not self.empty():
            self.get()
            self.task_done()
        log.info("emptied")

    def enqueue(self, item: QueueItem):
        log.info(f"enqueue: {item}")
        if item is None:  # Sentinel value
            self._clear()
        self.put(item)

    def remove_lower_priority(self, base: QueueItem):
        temp_pq = PriorityQueue()
        while not self.empty():
            item = self.get()
            if item is None:  # Sentinel value
                self.task_done()
                self._clear()
                self.put(None)
                return
            if item <= base:
                temp_pq.put(item)
            else:
                self.task_done()
                log.info(f"dequeue: {item}")
        while not temp_pq.empty():
            self.put(temp_pq.get())
