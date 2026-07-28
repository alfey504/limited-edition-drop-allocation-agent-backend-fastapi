import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.allocation import AllocationRecommendation


class AllocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self,
        conversation_id: uuid.UUID,
        sneaker_id: int,
        total_inventory: int,
        allocation: dict[str, int],
        reasoning: str,
    ) -> AllocationRecommendation:
        record = AllocationRecommendation(
            conversation_id=conversation_id,
            sneaker_id=sneaker_id,
            total_inventory=total_inventory,
            allocation=allocation,
            reasoning=reasoning,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_for_conversation(
        self, conversation_id: uuid.UUID
    ) -> list[AllocationRecommendation]:
        result = await self._session.execute(
            select(AllocationRecommendation)
            .where(AllocationRecommendation.conversation_id == conversation_id)
            .order_by(AllocationRecommendation.created_at.desc())
        )
        return list(result.scalars().all())
