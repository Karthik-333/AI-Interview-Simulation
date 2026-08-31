"""Application exception hierarchy and FastAPI-safe error payloads."""


class AppError(Exception):
    """Base class for expected application failures."""

    status_code = 500
    code = "application_error"

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class ResourceNotFoundError(AppError):
    status_code = 404
    code = "not_found"


class PersistenceError(AppError):
    status_code = 500
    code = "persistence_error"


class ExternalServiceError(AppError):
    status_code = 503
    code = "external_service_unavailable"


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"
