from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_active_user
from repositories.user import create_user, check_user_exists, login_user
from models.user import User
from db.dependencies import get_session
from schemas.user import UserCreate, UserLogin
from core.security import hash_password, create_access_token

router = APIRouter(tags=["users"])

@router.get("/me")
async def read_me(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str | bool | int]:
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
    }

@router.post("/create")
async def create_new_user(
    new_user: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:

    if await check_user_exists(session, new_user.email):
        return {"message": "User with this email already exists"}

    print(f"new_user.password: {new_user.password}", flush=True)
    new_user.password = hash_password(new_user.password)
    assert new_user.password, "Password hashing failed, got empty string"

    newly_created_user = await create_user(
        session,
        email=new_user.email,
        hashed_password=new_user.password,
    )

    print(f"hashed_password: {newly_created_user.hashed_password}", flush=True)
    return {"message": f"User {newly_created_user.email} created successfully"}

@router.get("/login")
async def login(
    UserLogin: UserLogin,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    logged_in_user = await login_user(
        session,
        UserLogin.email,
        UserLogin.password,
    )
    if not logged_in_user:
        return {"message": "Invalid email or password"}

    user_token = create_access_token(subject=str(logged_in_user.id))
    return {"token": user_token}

@router.get("/token-check")
async def token_check(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    return {"message": f"Token is valid for user {current_user.email}"}