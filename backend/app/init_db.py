from app.core.database import engine
from app.models.base import Base

# Import models so SQLAlchemy knows they exist
import app.models  # noqa: F401 - ensures all tables are registered


Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")