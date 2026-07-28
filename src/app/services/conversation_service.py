import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation
from app.db.models.message import Message, MessageRole
from app.repositories.conversation_repository import ConversationRepository
from app.services.exceptions import ConversationAccessDeniedError, ConversationNotFoundError


class ConversationService:
    """
    Owns conversation CRUD, ownership enforcement, and the transaction boundary
    around them. Does not yet invoke the agent — that lands once agent/graph.py
    exists; for now this only covers what's independently verifiable.
    """

    def __init__(self, session: AsyncSession, conversation_repository: ConversationRepository) -> None:
        self._session = session
        self._conversations = conversation_repository

    async def start_conversation(self, user_id: uuid.UUID) -> Conversation:
        conversation = await self._conversations.create(user_id)
        await self._session.commit()
        return conversation

    async def get_conversation_for_user(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Conversation:
        conversation = await self._conversations.get(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"No conversation with id {conversation_id}.")
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedError(
                f"Conversation {conversation_id} does not belong to user {user_id}."
            )
        return conversation

    async def list_conversations(self, user_id: uuid.UUID) -> list[Conversation]:
        return await self._conversations.list_for_user(user_id)

    async def record_user_message(self, conversation_id: uuid.UUID, content: str) -> Message:
        message = await self._conversations.add_message(
            conversation_id=conversation_id, role=MessageRole.USER, content=content
        )
        await self._session.commit()
        return message

    async def record_assistant_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        tool_calls: dict | None = None,
    ) -> Message:
        message = await self._conversations.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            tool_calls=tool_calls,
        )
        await self._session.commit()
        return message
