from fastapi import APIRouter, HTTPException

from app.core.tasks import task_status

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/{task_id}")
def get_task(task_id: str):
    result = task_status(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result
