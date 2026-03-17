from fastapi import APIRouter, Depends
from auth.dependencies import get_current_active_user
from models.user import User

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