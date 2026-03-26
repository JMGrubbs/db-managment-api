from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import oauth2_scheme, decode_access_token
from db.dependencies import get_session
from repositories.user import get_user_by_id
from repositories.jwt_token_blacklist import is_token_blacklisted_db, insert_blacklisted_token
from models.user import User

async def check_token_blacklist(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> bool:
    try:
        payload = decode_access_token(token)
        token_jti = payload.get("jti")
        if not token_jti:
            return True
    except Exception:
        return True

    return await is_token_blacklisted_db(session, token_jti)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_blacklisted = await check_token_blacklist(token, session)
    if token_blacklisted:
        raise credentials_exception

    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception

        user_id = int(sub)
    except Exception:
        raise credentials_exception

    user = await get_user_by_id(session, user_id)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def blacklist_current_token(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> bool:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        token_jti = payload.get("jti")
        if not token_jti:
            raise credentials_exception
    except Exception as e:
        raise credentials_exception

    insert_blacklisted_token_status = await insert_blacklisted_token(session, token_jti)
    return bool(insert_blacklisted_token_status)