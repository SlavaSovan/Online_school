from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.auth.models import RefreshToken
from app.auth.utils import hash_refresh_token


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_token(self, usr_id: str, token: str, exp: str) -> RefreshToken:
        user_id = int(usr_id)
        expires_at = datetime.fromtimestamp(float(exp))

        token_hash = hash_refresh_token(token)
        rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)

        self.db.add(rt)
        await self.db.commit()
        await self.db.refresh(rt)
        return rt

    async def get_token(self, token: str) -> Optional[RefreshToken]:
        token_hash = hash_refresh_token(token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.scalar(stmt)
        return result

    async def revoke_token(self, token: str) -> bool:
        refresh_token = await self.get_token(token)
        if refresh_token:
            await self.db.delete(refresh_token)
            await self.db.commit()
            return True
        return False

    async def revoke_all_user_tokens(self, user_id: int) -> bool:
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
        refresh_tokens = await self.db.scalars(stmt)
        refresh_tokens = refresh_tokens.all()
        if refresh_tokens:
            for rt in refresh_tokens:
                await self.db.delete(rt)
            await self.db.commit()
            return True
        return False

    async def is_token_revoked(self, token: str) -> bool:
        refresh_token = await self.get_token(token)
        return refresh_token is None

    async def delete_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        stmt = select(RefreshToken).where(RefreshToken.expires_at < now)
        refresh_tokens = await self.db.scalars(stmt).all()
        if refresh_tokens:
            for rt in refresh_tokens:
                await self.db.delete(rt)
            await self.db.commit()
            return True
        return False
