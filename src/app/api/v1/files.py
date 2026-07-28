from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.config import Settings, get_settings
from app.db.models.user import User
from app.repositories.report_repository import ReportRepository

router = APIRouter(tags=["files"])


@router.get("/file/{filename}")
async def download_file(
    filename: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    # filename is attacker-controlled; reject anything that could escape reports_dir
    # (../ traversal, or an absolute path — pathlib silently discards the base
    # when joined with an absolute path string) before it's ever used as a path.
    reports_dir = Path(settings.reports_dir).resolve()
    candidate = (reports_dir / filename).resolve()
    if not candidate.is_relative_to(reports_dir):
        raise not_found

    report = await ReportRepository(session).get_by_document(filename, current_user.id)
    if report is None:
        raise not_found

    if not candidate.is_file():
        raise not_found

    return FileResponse(candidate, media_type="application/pdf", filename=filename)
