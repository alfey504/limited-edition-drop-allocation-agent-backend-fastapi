from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.deps import get_database, get_forecasting_client, get_sneaker_client
from app.api.v1.router import router
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    database = get_database()
    await database.create_all()
    logger.info("Startup complete: schema ensured against Neon.")

    yield

    await database.dispose()
    await get_sneaker_client().aclose()
    await get_forecasting_client().aclose()
    logger.info("Shutdown complete: engine and HTTP clients closed.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Limited Edition Drop Allocation Agent",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()
