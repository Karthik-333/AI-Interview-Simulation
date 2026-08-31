"""Small in-process task queue with explicit status for optional async work."""

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from threading import Lock
from uuid import uuid4

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="interview-task")
_tasks: dict[str, Future] = {}
_lock = Lock()


def enqueue(function, *args, **kwargs) -> str:
    """Queue work and return a stable task identifier."""
    task_id = uuid4().hex
    with _lock:
        _tasks[task_id] = _executor.submit(function, *args, **kwargs)
    return task_id


def task_status(task_id: str) -> dict | None:
    """Return queued/running/completed state and result when available."""
    with _lock:
        future = _tasks.get(task_id)
    if future is None:
        return None
    if not future.done():
        return {"task_id": task_id, "status": "running"}
    if future.exception() is not None:
        return {"task_id": task_id, "status": "failed", "error": str(future.exception())}
    return {"task_id": task_id, "status": "completed", "result": future.result()}
