from __future__ import annotations

import queue
from typing import Optional

from app.adversarial.models import IOCEnvelope


class SharedQueueManager:
    def __init__(self, maxsize: int = 0) -> None:
        self._queue: queue.Queue[IOCEnvelope] = queue.Queue(maxsize=maxsize)

    def enqueue(self, envelope: IOCEnvelope) -> None:
        self._queue.put(envelope)

    def dequeue(self, timeout_seconds: float = 2.0) -> Optional[IOCEnvelope]:
        try:
            return self._queue.get(timeout=timeout_seconds)
        except queue.Empty:
            return None

    def task_done(self) -> None:
        self._queue.task_done()

    def size(self) -> int:
        return self._queue.qsize()
