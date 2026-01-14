from typing import Optional
from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate

class UserService:
    def __init__(self, userRepoitory: UserRepository) -> None:
        self.repo = userRepoitory

    def login(self, user_login: UserLogin) -> User:
        """
        사용자 로그인을 처리한다.

        Args: 
            user_login (UserLogin) : 로그인 요청 데이터(이메일, 비밀번호)

        Returns :
            Optional[user] : 로그인 성공시 User 객체, 실패 시 None
        """
        # 1. 존재하는 User인지 확인
        user = self.repo.get_user_by_email(user_login.email)

        if not user :
            raise ValueError("User not Found.")
        
        # 2. 존재하는 user라면 비밀번호 값의 일치 여부 확인
        if user_login.password != user.password:
            raise ValueError("Invalid ID/PW")
        
        return user
        
        
    def register_user(self, new_user: User) -> Optional[User]:
        """
        새로운 사용자를 등록한다. 
        Args: 
            new_user (User) : 등록할 사용자 정보 객체

        Returns :
            Optional[User] : 등록 성공시 저장된 User 객체, 이미 존재할 경우 None
        """
        # 1. 기존에 존재하는 user인지 확인
        # new_user = self.repo ~ 로 쓰면 new user가 가지고 있는 가입하려는 사람 정보가 사라짐 -> 다른 변수에다가 할당해서 기존에 있는 유저인지 아닌지 확인해줘야 함.
        existing_user = self.repo.get_user_by_email(new_user.email)

        if existing_user : 
            raise ValueError("User already Exists.")

        # 2. 가입된 사람이 아니라면 등록 진행
        # new_user는 단순히 데이터 덩어리라서 repo를 가지고 있지 않음. repo를 가지고 있는 건 self라서 self.repo로 써줘야 함.
        saved_user = self.repo.save_user(new_user)

        return new_user


    def delete_user(self, email: str) -> Optional[User]:
        """
        이메일 기반으로 user를 삭제한다. 

        Args :
            email (str) : 삭제할 사용자의 이메일
        
        
        Returns : 
            Optional[User]: 삭제된 User 객체, 사용자가 없을 경우 None
        """
        # 1. 기존에 존재하는 user인지 확인
        target_user = self.repo.get_user_by_email(email)

        if not target_user:
            raise ValueError("User not Found.")

        # 2. 존재하는 유저라면 delete_user 실행
        self.repo.delete_user(target_user)
        
        return target_user

    def update_user_pwd(self, user_update: UserUpdate) -> Optional[User]:
        """
        사용자의 비밀번호를 변경한다.
        
        Args:
            user_update (UserUpdate): 변경할 정보가 담긴 객체 (이메일, 새 비밀번호)
            
        Returns:
            Optional[User]: 업데이트된 User 객체, 사용자가 없을 경우 None
        """
        # 1. 정보를 update할 user의 정보를 받아고기
        updated_user = self.repo.get_user_by_email(user_update.email)
        
        # 2. 기존에 존재하는 user인지 확인
        if not updated_user:
            raise ValueError("User not Found.")

        # 3. 존재하는 user라면 정보 update 진행 후 DB에 저장
        updated_user.password = user_update.new_password

        self.repo.save_user(updated_user)

        return updated_user
        