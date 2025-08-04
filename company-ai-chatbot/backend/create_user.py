from database import SessionLocal
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(username, plain_password, name, role, departments):
    db = SessionLocal()
    try:
        hashed_password = pwd_context.hash(plain_password)
        new_user = User(
            username=username,
            hashed_password=hashed_password,
            name=name,
            role=role,
            departments=departments
        )
        db.add(new_user)
        db.commit()
        print(f"Created user: {username}")
    except Exception as e:
        print("Error creating user:", e)
    finally:
        db.close()

if __name__ == "__main__":
    create_user(
        username="admin",
        plain_password="admin123",
        name="System Administrator",
        role="admin",
        departments=["all"]
    )
