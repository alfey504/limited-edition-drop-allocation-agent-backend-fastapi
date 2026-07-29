from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.config import Settings, get_settings
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_auth_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(session, UserRepository(session), settings)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest, auth_service: AuthService = Depends(_get_auth_service)
) -> UserOut:
    # EmailAlreadyRegisteredError -> 409, handled globally (core/exceptions.py)
    user = await auth_service.register(body.email, body.password)
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest, auth_service: AuthService = Depends(_get_auth_service)
) -> TokenResponse:
    # InvalidCredentialsError -> 401, handled globally (core/exceptions.py)
    token = await auth_service.authenticate(body.email, body.password)
    return TokenResponse(access_token=token)
