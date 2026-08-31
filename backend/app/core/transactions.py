"""Reusable transaction boundary for service operations."""

from collections.abc import Generator
from contextlib import contextmanager
from sqlalchemy.orm import Session


@contextmanager
def transaction(db: Session) -> Generator[Session, None, None]:
    """Commit on success and rollback before re-raising any database error."""
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
