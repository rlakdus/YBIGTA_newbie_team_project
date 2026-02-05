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
        # 1. 이메일 존재 여부 확인 (SQLite/MySQL 공용 문법)
        check_query = text("SELECT email FROM users WHERE email = :email")
        existing = self.db.execute(check_query, {"email": user.email}).fetchone()

        if existing:
            # 2. 존재하면 UPDATE 실행
            update_query = text("""
                UPDATE users 
                SET password = :password, username = :username 
                WHERE email = :email
            """)
            self.db.execute(update_query, {
                "email": user.email,
                "password": user.password,
                "username": user.username
            })
        else:
            # 3. 존재하지 않으면 INSERT 실행
            insert_query = text("""
                INSERT INTO users (email, password, username) 
                VALUES (:email, :password, :username)
            """)
            self.db.execute(insert_query, {
                "email": user.email,
                "password": user.password,
                "username": user.username
            })

        self.db.commit()
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        query = text("""
        SELECT email, password, username
        FROM users
        WHERE email = :email
        """)

        # result[0], result[1] 처럼 인덱스로 접근하여 모든 DB 라이브러리 호환성 확보
        result = self.db.execute(query, {"email": email}).fetchone()

        if result is None:
            return None

        return User(
            email=result[0],
            password=result[1],
            username=result[2],
        )

    def delete_user(self, user: User) -> User:
        query = text("""
        DELETE FROM users
        WHERE email = :email
        """)

        self.db.execute(query, {"email": user.email})
        self.db.commit()
        return user