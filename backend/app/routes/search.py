import csv
import json
import logging
from datetime import datetime
from io import StringIO
from typing import Dict

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
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
    try:
        service = ExportService(session)
        csv_data = await service.export_dialog_csv(client_id)

        return StreamingResponse(
            iter([csv_data]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=dialog_{client_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )
    except Exception as e:
        logger.error(f"Error exporting dialog CSV for client_id {client_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export dialog CSV: {str(e)}"
        )


@router.get("/export/dialog/{client_id}.json")
async def export_dialog_json(
    client_id: str, session: AsyncSession = Depends(get_session)
):
    """Export dialog as JSON"""
    try:
        service = ExportService(session)
        json_data = await service.export_dialog_json(client_id)
        return json_data
    except Exception as e:
        logger.error(f"Error exporting dialog JSON for client_id {client_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export dialog JSON: {str(e)}"
        )


@router.get("/export/report")
async def export_report(
    hours: int = Query(24, ge=1, le=720), session: AsyncSession = Depends(get_session)
):
    """Export analytics report"""
    try:
        service = ExportService(session)
        report = await service.export_analytics_report(hours=hours)
        return report
    except Exception as e:
        logger.error(f"Error exporting analytics report (hours={hours}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export analytics report: {str(e)}"
        )


@router.post("/export/results")
async def export_search_results(
    search_params: Dict = Body(...), session: AsyncSession = Depends(get_session)
):
    """Export search results as CSV or JSON"""
    try:
        service = SearchService(session)
        result = await service.search_messages(
            query=search_params.get("q", ""),
            client_id=search_params.get("client_id"),
            scenario=search_params.get("scenario"),
            min_confidence=search_params.get("min_confidence", 0.0),
            limit=search_params.get("limit", 1000),  # Large limit for export
            offset=0,
        )
        
        format_type = search_params.get("format", "csv")
        
        if format_type == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "ID", "Client ID", "Timestamp", "Type", "Content", 
                "Scenario", "Confidence", "Reasoning", "Priority"
            ])
            
            for msg in result.get("messages", []):
                classification = msg.get("classification") or {}
                writer.writerow([
                    msg.get("id", ""),
                    msg.get("client_id", ""),
                    msg.get("created_at", ""),
                    msg.get("message_type", ""),
                    msg.get("content", ""),
                    classification.get("scenario") if isinstance(classification, dict) else "N/A",
                    f"{classification.get('confidence', 0) * 100:.2f}%" if isinstance(classification, dict) and classification.get("confidence") is not None else "N/A",
                    classification.get("reasoning") if isinstance(classification, dict) else "",
                    msg.get("priority") or "N/A",
                ])
            
            csv_data = output.getvalue()
            return StreamingResponse(
                iter([csv_data]),
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": f"attachment; filename=search_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"},
            )
        else:
            return {
                "export_date": datetime.utcnow().isoformat(),
                "search_params": search_params,
                "total": result.get("total", 0),
                "count": result.get("count", 0),
                "messages": result.get("messages", []),
            }
    except Exception as e:
        logger.error(f"Error exporting search results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export search results: {str(e)}"
        )
