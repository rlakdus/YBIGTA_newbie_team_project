from fastapi import APIRouter, HTTPException, Depends, status
from app.user.user_schema import User, UserLogin, UserUpdate, UserDeleteRequest
from app.user.user_service import UserService
from app.dependencies import get_user_service
from app.responses.base_response import BaseResponse

user = APIRouter(prefix="/api/user")


@user.post("/login", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def login_user(user_login: UserLogin, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    사용자 로그인을 처리하고 정보를 반환합니다.

    Args:
        user_login (UserLogin): 로그인에 필요한 이메일 및 비밀번호 정보
    
    Returns:
        BaseResponse[User]: 로그인 성공 시 사용자 데이터와 성공 메시지
    """
    try:
        user_data: User = service.login(user_login)
        return BaseResponse(status="success", data=user_data, message="Login Success.") 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@user.post("/register", response_model=BaseResponse[User], status_code=status.HTTP_201_CREATED)
def register_user(user: User, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    새로운 사용자 계정을 등록합니다.

    Args:
        user (User): 가입할 사용자의 인적 사항 및 계정 정보
    
    Returns:
        BaseResponse[User]: 등록 완료된 사용자 정보
    """
    try:
        registered_user = service.register_user(user)
        return BaseResponse(status="success", data=registered_user, message="User registration success.") 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@user.delete("/delete", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def delete_user(user_delete_request: UserDeleteRequest, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    이메일 정보를 기반으로 사용자 계정을 삭제합니다.

    Args:
        user_delete_request (UserDeleteRequest): 삭제 요청 이메일 정보
    
    Returns:
        BaseResponse[User]: 삭제된 사용자 정보 확인
    """
    try:
        deleted_user = service.delete_user(user_delete_request.email)
        return BaseResponse(status="success", data=deleted_user, message="User Deletion Success.") 
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@user.put("/update-password", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def update_user_password(user_update: UserUpdate, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    사용자의 비밀번호를 변경합니다.

    Args:
        user_update (UserUpdate): 비밀번호 변경에 필요한 이메일 및 신규 비밀번호 정보
    
    Returns:
        BaseResponse[User]: 비밀번호가 업데이트된 사용자 정보
    """
    try:
        updated_user = service.update_user_pwd(user_update)
        return BaseResponse(status="success", data=updated_user, message="User password update success.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))