import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.language_models import BaseChatModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import make_agent_graph_factory
from app.api.deps import get_current_user, get_db_session, get_forecasting_client, get_llm_client, get_sneaker_client
from app.core.config import Settings, get_settings
from app.db.models.user import User
from app.integrations.forecasting_api_client import ForecastingApiClient
from app.integrations.sneaker_api_client import SneakerApiClient
from app.repositories.allocation_repository import AllocationRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.report_repository import ReportRepository
from app.schemas.conversation import ConversationDetailOut, ConversationOut
from app.schemas.message import MessageCreate, MessageOut
from app.services.conversation_service import ConversationService
from app.services.exceptions import ConversationAccessDeniedError, ConversationNotFoundError

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _get_conversation_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    llm: BaseChatModel = Depends(get_llm_client),
    sneaker_client: SneakerApiClient = Depends(get_sneaker_client),
    forecasting_client: ForecastingApiClient = Depends(get_forecasting_client),
) -> ConversationService:
    graph_factory = make_agent_graph_factory(
        llm,
        sneaker_client,
        forecasting_client,
        AllocationRepository(session),
        ReportRepository(session),
        Path(settings.reports_dir),
    )
    return ConversationService(session, ConversationRepository(session), graph_factory)


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def start_conversation(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(_get_conversation_service),
) -> ConversationOut:
    conversation = await conversation_service.start_conversation(current_user.id)
    return ConversationOut.model_validate(conversation)


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(_get_conversation_service),
) -> list[ConversationOut]:
    conversations = await conversation_service.list_conversations(current_user.id)
    return [ConversationOut.model_validate(conversation) for conversation in conversations]


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(_get_conversation_service),
) -> ConversationDetailOut:
    try:
        conversation = await conversation_service.get_conversation_for_user(
            conversation_id, current_user.id
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConversationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return ConversationDetailOut.model_validate(conversation)


@router.post("/{conversation_id}/messages", response_model=MessageOut)
async def send_message(
    conversation_id: uuid.UUID,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(_get_conversation_service),
) -> MessageOut:
    try:
        message = await conversation_service.send_message(
            conversation_id, current_user.id, body.content
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConversationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return MessageOut.model_validate(message)
