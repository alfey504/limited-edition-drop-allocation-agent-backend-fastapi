from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.integrations.exceptions import IntegrationError
from app.services.exceptions import (
    ConversationAccessDeniedError,
    ConversationNotFoundError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    ServiceError,
)

logger = get_logger(__name__)

# The mapping lives here, not on the exceptions themselves — services/exceptions.py
# stays framework-agnostic (a service raising an HTTP status code would leak this
# layer's concerns into code that has no business knowing what HTTP is).
_SERVICE_ERROR_STATUS_CODES: dict[type[ServiceError], int] = {
    EmailAlreadyRegisteredError: status.HTTP_409_CONFLICT,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    ConversationNotFoundError: status.HTTP_404_NOT_FOUND,
    ConversationAccessDeniedError: status.HTTP_403_FORBIDDEN,
}


async def handle_service_error(request: Request, exc: ServiceError) -> JSONResponse:
    status_code = _SERVICE_ERROR_STATUS_CODES.get(type(exc), status.HTTP_400_BAD_REQUEST)
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


async def handle_integration_error(request: Request, exc: IntegrationError) -> JSONResponse:
    """A tool call (or anything else) hit the sneaker/forecasting API and it failed.
    That's an upstream problem, not something the client did wrong — 502, not 500."""
    logger.error("Upstream integration failure on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "An upstream service is currently unavailable. Please try again."},
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error."},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ServiceError, handle_service_error)
    app.add_exception_handler(IntegrationError, handle_integration_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
