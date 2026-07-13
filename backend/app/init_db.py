from app.core.database import engine
from app.models.base import Base

# Import models so SQLAlchemy knows they exist
from app.models.interview import InterviewSession


Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")