from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.jwt_token_blacklist import JwtTokenBlacklist
from datetime import datetime, timedelta

async def is_token_blacklisted_db(session: AsyncSession, jti: str) -> bool:
    result = await session.execute(
        select(JwtTokenBlacklist).where(JwtTokenBlacklist.token == jti)
    )
    if result.scalar() is not None:
        return True
    return False

async def load_recent_blacklisted_tokens(session: AsyncSession, minutes: int = 60) -> list[str]:
    cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
    result = await session.execute(
        select(JwtTokenBlacklist.token).where(JwtTokenBlacklist.blacklisted_at >= cutoff_time)
    )
    return [row[0] for row in result.fetchall()]

async def insert_blacklisted_token(session: AsyncSession, jti: str) -> bool:
    print(f"Inserting blacklisted token with jti: {jti}", flush=True)
    new_entry = JwtTokenBlacklist(token=jti, blacklisted_at=datetime.utcnow())
    session.add(new_entry)
    await session.commit()
    return True