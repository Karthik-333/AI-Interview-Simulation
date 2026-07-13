from app.core.database import SessionLocal
from app.models.interview import InterviewSession

# db = SessionLocal()
# interview = InterviewSession(
#     user_name="Karthik",
#     score=85
# )
# Create 
# print("Object created")

# db.add(interview)

# print("Added to session")

# db.commit()

# print("Committed to database")

# db.close()

# Read
# db = SessionLocal()
# sessions = db.query(InterviewSession).all()

# for session in sessions:
#     print(
#         session.id,
#         session.user_name,
#         session.score
#     )

# db.close()
# Update
# db = SessionLocal()

# session = db.query(InterviewSession).first()

# print("Before:", session.score)

# session.score = 95

# db.commit()

# print("After:", session.score)

# db.close()
#delete
db = SessionLocal()

session = db.query(InterviewSession)\
            .filter(InterviewSession.id == 4)\
            .first()

if session:
    db.delete(session)
    db.commit()
    print("Row deleted")

db.close()