from core.database import SessionLocal
from models import User

def init_db():
    db = SessionLocal()
    user = User(name="Initial User", email="initial@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.close()

if __name__ == "__main__":
    init_db()
