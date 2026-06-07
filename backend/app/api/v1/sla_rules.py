import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import require_owner
from backend.app.db.session import get_db
from backend.app.models.sla_rule import SlaRule
from backend.app.schemas.sla_rule import SlaRuleCreate, SlaRuleResponse, SlaRuleUpdate

router = APIRouter(prefix="/sla-rules", tags=["sla-rules"], dependencies=[Depends(require_owner)])


@router.get("", response_model=list[SlaRuleResponse])
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SlaRule).order_by(SlaRule.priority))
    return list(result.scalars().all())


@router.post("", response_model=SlaRuleResponse, status_code=201)
async def create_rule(data: SlaRuleCreate, db: AsyncSession = Depends(get_db)):
    rule = SlaRule(**data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=SlaRuleResponse)
async def update_rule(rule_id: uuid.UUID, data: SlaRuleUpdate, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException, status as http_status

    rule = await db.get(SlaRule, rule_id)
    if not rule:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Rule not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException, status as http_status

    rule = await db.get(SlaRule, rule_id)
    if not rule:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
