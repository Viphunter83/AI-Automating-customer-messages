from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_session
from app.models.database import ResponseTemplate, ScenarioType, Keyword, OperatorFeedback, Classification
from app.models.schemas import ResponseTemplateCreate, ResponseTemplateUpdate, ResponseTemplateResponse
from app.services.model_retraining import ModelRetrainingService
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ========== RESPONSE TEMPLATES ==========

@router.get("/templates", response_model=list[ResponseTemplateResponse])
async def list_templates(
    session: AsyncSession = Depends(get_session),
    active_only: bool = Query(True)
):
    """Get all response templates"""
    query = select(ResponseTemplate)
    
    if active_only:
        query = query.where(ResponseTemplate.is_active == True)
    
    result = await session.execute(query.order_by(ResponseTemplate.scenario_name))
    templates = result.scalars().all()
    
    return [
        ResponseTemplateResponse(
            id=str(t.id),
            scenario_name=t.scenario_name,
            template_text=t.template_text,
            requires_params=t.requires_params,
            version=t.version,
            is_active=t.is_active,
            updated_at=t.updated_at,
        )
        for t in templates
    ]

@router.get("/templates/{scenario_name}", response_model=ResponseTemplateResponse)
async def get_template(
    scenario_name: str,
    session: AsyncSession = Depends(get_session)
):
    """Get specific template by scenario"""
    try:
        scenario = ScenarioType[scenario_name]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario: {scenario_name}"
        )
    
    result = await session.execute(
        select(ResponseTemplate).where(ResponseTemplate.scenario_name == scenario)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No template for {scenario_name}"
        )
    
    return ResponseTemplateResponse(
        id=str(template.id),
        scenario_name=template.scenario_name,
        template_text=template.template_text,
        requires_params=template.requires_params,
        version=template.version,
        is_active=template.is_active,
        updated_at=template.updated_at,
    )

@router.post("/templates/{scenario_name}", response_model=ResponseTemplateResponse)
async def update_template(
    scenario_name: str,
    update_data: ResponseTemplateUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update response template"""
    try:
        scenario = ScenarioType[scenario_name]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario: {scenario_name}"
        )
    
    result = await session.execute(
        select(ResponseTemplate).where(ResponseTemplate.scenario_name == scenario)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No template for {scenario_name}"
        )
    
    # Update fields
    if update_data.template_text:
        template.template_text = update_data.template_text
    
    if update_data.requires_params is not None:
        template.requires_params = update_data.requires_params
    
    if update_data.is_active is not None:
        template.is_active = update_data.is_active
    
    template.version += 1
    template.updated_at = datetime.utcnow()
    
    await session.commit()
    
    logger.info(f"✅ Updated template {scenario_name} to v{template.version}")
    
    return ResponseTemplateResponse(
        id=str(template.id),
        scenario_name=template.scenario_name,
        template_text=template.template_text,
        requires_params=template.requires_params,
        version=template.version,
        is_active=template.is_active,
        updated_at=template.updated_at,
    )

# ========== FEEDBACK ANALYTICS ==========

@router.get("/feedback/summary")
async def get_feedback_summary(
    hours: int = Query(24, ge=1, le=720),
    session: AsyncSession = Depends(get_session)
):
    """Get feedback summary for last N hours"""
    service = ModelRetrainingService(session)
    summary = await service.get_feedback_summary(hours=hours)
    
    return {
        "period_hours": hours,
        "timestamp": datetime.utcnow().isoformat(),
        **summary
    }

@router.get("/feedback/misclassified")
async def get_misclassified(
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session)
):
    """Get incorrectly classified messages"""
    service = ModelRetrainingService(session)
    messages = await service.get_misclassified_messages(limit=limit)
    
    return {
        "count": len(messages),
        "messages": messages,
    }

@router.get("/retraining/data")
async def get_retraining_data(
    session: AsyncSession = Depends(get_session)
):
    """Get data for model retraining"""
    service = ModelRetrainingService(session)
    training_data = await service.generate_retraining_data()
    keywords = await service.update_keywords_from_feedback()
    
    return {
        "training": training_data,
        "keywords": keywords,
    }

# ========== KEYWORDS MANAGEMENT ==========

@router.get("/keywords")
async def list_keywords(
    scenario: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """Get all keywords or filter by scenario"""
    query = select(Keyword).order_by(Keyword.priority.desc())
    
    if scenario:
        try:
            scenario_enum = ScenarioType[scenario]
            query = query.where(Keyword.scenario_name == scenario_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scenario: {scenario}"
            )
    
    result = await session.execute(query)
    keywords = result.scalars().all()
    
    return {
        "filter": scenario or "all",
        "count": len(keywords),
        "keywords": [
            {
                "id": str(k.id),
                "scenario": str(k.scenario_name.value),
                "keyword": k.keyword,
                "priority": k.priority,
            }
            for k in keywords
        ]
    }

@router.post("/keywords")
async def add_keyword(
    scenario: str = Query(...),
    keyword: str = Query(..., min_length=1),
    priority: int = Query(5, ge=1, le=10),
    session: AsyncSession = Depends(get_session)
):
    """Add new keyword (via query params for compatibility with frontend)"""
    try:
        scenario_enum = ScenarioType[scenario]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario: {scenario}"
        )
    
    # Check if keyword already exists for this scenario
    existing = await session.execute(
        select(Keyword).where(
            Keyword.scenario_name == scenario_enum,
            Keyword.keyword == keyword.lower()
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Keyword '{keyword}' already exists for {scenario}"
        )
    
    new_keyword = Keyword(
        id=uuid4(),
        scenario_name=scenario_enum,
        keyword=keyword.lower(),
        priority=priority,
    )
    
    session.add(new_keyword)
    await session.commit()
    
    logger.info(f"✅ Added keyword '{keyword}' for {scenario}")
    
    return {
        "id": str(new_keyword.id),
        "scenario": scenario,
        "keyword": keyword,
        "priority": priority,
    }

@router.delete("/keywords/{keyword_id}")
async def delete_keyword(
    keyword_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Delete keyword"""
    try:
        keyword_uuid = UUID(keyword_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid keyword ID"
        )
    
    result = await session.execute(
        select(Keyword).where(Keyword.id == keyword_uuid)
    )
    keyword = result.scalar_one_or_none()
    
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found"
        )
    
    await session.delete(keyword)
    await session.commit()
    
    logger.info(f"✅ Deleted keyword {keyword_id}")
    
    return {"message": "Keyword deleted"}

# ========== STATISTICS ==========

@router.get("/stats/classifications")
async def get_classification_stats(
    hours: int = Query(24, ge=1, le=720),
    session: AsyncSession = Depends(get_session)
):
    """Get classification statistics"""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    result = await session.execute(
        select(
            Classification.detected_scenario,
            func.count(Classification.id).label('count'),
            func.avg(Classification.confidence).label('avg_confidence')
        )
        .where(Classification.created_at >= cutoff_time)
        .group_by(Classification.detected_scenario)
    )
    
    stats = result.all()
    
    return {
        "period_hours": hours,
        "scenarios": [
            {
                "scenario": str(row[0].value),
                "count": row[1],
                "avg_confidence": float(row[2]) if row[2] else 0,
            }
            for row in stats
        ]
    }

@router.get("/stats/messages")
async def get_message_stats(
    session: AsyncSession = Depends(get_session)
):
    """Get message statistics"""
    from app.models.database import Message, MessageType
    
    # Total messages
    total_result = await session.execute(select(func.count(Message.id)))
    total = total_result.scalar() or 0
    
    # By type
    type_result = await session.execute(
        select(Message.message_type, func.count(Message.id).label('count'))
        .group_by(Message.message_type)
    )
    by_type = type_result.all()
    
    # Unique clients
    clients_result = await session.execute(
        select(func.count(func.distinct(Message.client_id)))
    )
    unique_clients = clients_result.scalar() or 0
    
    return {
        "total_messages": total,
        "unique_clients": unique_clients,
        "by_type": [
            {
                "type": str(row[0].value),
                "count": row[1],
            }
            for row in by_type
        ]
    }

