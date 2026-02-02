from typing import Optional
from sqlalchemy import text
from app.user.user_schema import User


class UserRepository:
    def __init__(self, db_session):
        """
        db_session:
        - 테스트 환경: SQLite session
        - 실제 환경: MySQL session
        """
        self.db = db_session

    def save_user(self, user: User) -> User:
        """
        email 기준으로
        - 없으면 INSERT
        - 있으면 UPDATE (UPSERT)
        """
        query = text("""
        INSERT INTO users (email, password, username)
        VALUES (:email, :password, :username)
        ON CONFLICT(email) DO UPDATE SET
            password = :password,
            username = :username
        """)

        self.db.execute(
            query,
            {
                "email": user.email,
                "password": user.password,
                "username": user.username,
            },
        )
        self.db.commit()
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        query = text("""
        SELECT email, password, username
        FROM users
        WHERE email = :email
        """)

        result = self.db.execute(query, {"email": email}).fetchone()

        if result is None:
            return None

        return User(
            email=result.email,
            password=result.password,
            username=result.username,
        )

    def delete_user(self, user: User) -> User:
        query = text("""
        DELETE FROM users
        WHERE email = :email
        """)

        self.db.execute(query, {"email": user.email})
        self.db.commit()
        return user
