from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError


class AuthService:
    def __init__(
        self, session: AsyncSession, user_repository: UserRepository, settings: Settings
    ) -> None:
        self._session = session
        self._users = user_repository
        self._settings = settings

    async def register(self, email: str, password: str) -> User:
        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError(f"{email} is already registered.")

        user = await self._users.create(email=email, hashed_password=hash_password(password))
        await self._session.commit()
        return user

    async def authenticate(self, email: str, password: str) -> str:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password.")

        return create_access_token({"user_id": str(user.id)}, settings=self._settings)
