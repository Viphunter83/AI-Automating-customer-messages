import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.export_service import ExportService
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/messages")
async def search_messages(
    q: str = Query("", min_length=0),
    client_id: str = Query(None),
    scenario: str = Query(None),
    min_confidence: float = Query(0.0, ge=0, le=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Search messages"""
    service = SearchService(session)
    result = await service.search_messages(
        query=q,
        client_id=client_id,
        scenario=scenario,
        min_confidence=min_confidence,
        limit=limit,
        offset=offset,
    )
    return result


@router.get("/dialogs")
async def search_dialogs(
    min_messages: int = Query(1, ge=1),
    has_feedback: bool = Query(None),
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """Search dialogs by criteria"""
    service = SearchService(session)
    dialogs = await service.search_dialogs(
        min_messages=min_messages, has_feedback=has_feedback, hours=hours, limit=limit
    )
    return {"count": len(dialogs), "dialogs": dialogs}


@router.get("/clients/autocomplete")
async def autocomplete_clients(
    prefix: str = Query("", min_length=0),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
):
    """Autocomplete client IDs"""
    service = SearchService(session)
    clients = await service.autocomplete_clients(prefix=prefix, limit=limit)
    return {"clients": clients}


@router.get("/export/dialog/{client_id}.csv")
async def export_dialog_csv(
    client_id: str, session: AsyncSession = Depends(get_session)
):
    """Export dialog as CSV"""
    service = ExportService(session)
    csv_data = await service.export_dialog_csv(client_id)

    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=dialog_{client_id}.csv"},
    )


@router.get("/export/dialog/{client_id}.json")
async def export_dialog_json(
    client_id: str, session: AsyncSession = Depends(get_session)
):
    """Export dialog as JSON"""
    service = ExportService(session)
    json_data = await service.export_dialog_json(client_id)
    return json_data


@router.get("/export/report")
async def export_report(
    hours: int = Query(24, ge=1, le=720), session: AsyncSession = Depends(get_session)
):
    """Export analytics report"""
    service = ExportService(session)
    report = await service.export_analytics_report(hours=hours)
    return report
