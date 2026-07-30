import uuid
from collections.abc import AsyncGenerator
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_core.language_models import BaseChatModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm import get_fallback_llms, get_llm
from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import Database
from app.integrations.forecasting_api_client import ForecastingApiClient
from app.integrations.sneaker_api_client import SneakerApiClient
from app.repositories.user_repository import UserRepository

_bearer_scheme = HTTPBearer()


@lru_cache
def get_database() -> Database:
    """Constructed once per process (get_settings() is itself cached), so the
    engine/connection pool is shared across requests rather than rebuilt on
    every one — get_db_session below only opens a new session per request,
    not a new engine."""
    return Database(get_settings())


@lru_cache
def get_sneaker_client() -> SneakerApiClient:
    """Memoized for the same reason as get_database — each client owns an
    httpx.AsyncClient with its own connection pool; rebuilding one per request
    would throw away keep-alive connections every time."""
    return SneakerApiClient(get_settings())


@lru_cache
def get_forecasting_client() -> ForecastingApiClient:
    return ForecastingApiClient(get_settings())


@lru_cache
def get_llm_client() -> BaseChatModel:
    return get_llm(get_settings())


@lru_cache
def get_fallback_llm_clients() -> list[BaseChatModel]:
    """Memoized for the same reason as get_llm_client — one shared client per
    fallback model, not rebuilt on every request."""
    return get_fallback_llms(get_settings())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_database().session():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials, settings)
        user_id = uuid.UUID(payload["user_id"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise unauthorized from exc

    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise unauthorized
    return user
