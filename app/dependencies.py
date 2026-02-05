from fastapi import Depends
from database.mysql_connection import SessionLocal
from app.user.user_repository import UserRepository
from app.user.user_service import UserService


# 1️⃣ DB session dependency
def get_db():
    """
    요청 하나당 DB session 하나 생성
    요청이 끝나면 자동으로 close
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 2️⃣ UserRepository dependency
def get_user_repository(db=Depends(get_db)) -> UserRepository:
    """
    DB session을 주입받아 UserRepository 생성
    """
    return UserRepository(db)


# 3️⃣ UserService dependency
def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    """
    UserRepository를 주입받아 UserService 생성
    """
    return UserService(repo)
