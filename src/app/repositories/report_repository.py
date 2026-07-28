import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.report import Report


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: uuid.UUID, document: str) -> Report:
        report = Report(user_id=user_id, document=document)
        self._session.add(report)
        await self._session.flush()
        return report

    async def get_by_document(self, document: str, user_id: uuid.UUID) -> Report | None:
        result = await self._session.execute(
            select(Report).where(Report.document == document, Report.user_id == user_id)
        )
        return result.scalar_one_or_none()
