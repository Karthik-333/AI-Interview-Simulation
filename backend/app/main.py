import time
from collections import defaultdict, deque
import logging

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.settings import API_VERSION, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS
from app.api.agents import router as agent_router
from app.api.auth import router as auth_router
from app.api.interviews import router as interview_router
from app.api.job_description import router as job_description_router
from app.api.mcp import router as mcp_router
from app.api.resume import router as resume_router
from app.api.tasks import router as tasks_router
from app.api.webhooks import router as webhook_router
from app.api.voice import router as voice_router


configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title="AI Interview Simulation", version="0.4.0")
_request_times: dict[str, deque[float]] = defaultdict(deque)
_metrics = {"requests_total": 0, "errors_total": 0}


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    _metrics["errors_total"] += 1
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}})


@app.middleware("http")
async def production_middleware(request: Request, call_next):
    now = time.monotonic()
    key = request.client.host if request.client else "unknown"
    bucket = _request_times[key]
    while bucket and now - bucket[0] >= RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_REQUESTS:
        return JSONResponse(status_code=429, content={"error": {"code": "rate_limited", "message": "Too many requests"}})
    bucket.append(now)
    _metrics["requests_total"] += 1
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        _metrics["errors_total"] += 1
        logger.exception("unhandled_request_error")
        raise
    response.headers["X-Process-Time-ms"] = f"{(time.perf_counter() - started) * 1000:.2f}"
    response.headers["X-API-Version"] = API_VERSION
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(interview_router)
app.include_router(job_description_router)
app.include_router(resume_router)
app.include_router(mcp_router)
app.include_router(agent_router)
app.include_router(tasks_router)
app.include_router(webhook_router)
app.include_router(voice_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(job_description_router, prefix="/api/v1")
app.include_router(resume_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(webhook_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")


@app.get("/health/live", tags=["Health"])
def liveness():
    return {"status": "ok"}


@app.get("/health/ready", tags=["Health"])
def readiness():
    from app.core.database import engine
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return {"status": "ready"}
    except Exception as exc:
        logger.warning("readiness_check_failed", exc_info=True)
        return JSONResponse(status_code=503, content={"status": "not_ready"})


@app.get("/metrics", tags=["Health"])
def metrics():
    """Expose lightweight Prometheus-compatible counters without a dependency."""
    return "\n".join(f"interview_api_{key} {value}" for key, value in _metrics.items()) + "\n"
