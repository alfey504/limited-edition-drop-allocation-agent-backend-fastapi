import uuid
from collections.abc import Callable

from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.message_mapping import (
    extract_final_response,
    extract_report_filename,
    to_langchain_messages,
)
from app.db.models.conversation import Conversation
from app.db.models.message import Message, MessageRole
from app.repositories.conversation_repository import ConversationRepository
from app.services.exceptions import ConversationAccessDeniedError, ConversationNotFoundError


class ConversationService:
    """
    Owns conversation CRUD, ownership enforcement, the transaction boundary
    around them, and orchestrating a turn through the agent.
    """

    def __init__(
        self,
        session: AsyncSession,
        conversation_repository: ConversationRepository,
        agent_graph_factory: Callable[[uuid.UUID, uuid.UUID], CompiledStateGraph],
    ) -> None:
        self._session = session
        self._conversations = conversation_repository
        self._agent_graph_factory = agent_graph_factory

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

    async def send_message(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID, content: str
    ) -> Message:
        """
        Runs one full turn: verifies ownership, loads prior history, runs the
        agent with that history plus the new message, and persists both the
        user's message and the agent's final response.
        """
        conversation = await self.get_conversation_for_user(conversation_id, user_id)
        history = to_langchain_messages(conversation.messages)

        await self.record_user_message(conversation_id, content)

        graph = self._agent_graph_factory(user_id, conversation_id)
        result = await graph.ainvoke({"messages": [*history, HumanMessage(content=content)]})

        response_content = extract_final_response(result["messages"])
        report_filename = extract_report_filename(result["messages"])
        tool_calls = {"report_filename": report_filename} if report_filename else None

        return await self.record_assistant_message(conversation_id, response_content, tool_calls)
