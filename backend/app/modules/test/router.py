from __future__ import annotations
from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db, require_project_access
from app.modules.test import models as tm
from app.modules.test.schemas import CaseCreate, PlanCreate, SuiteCreate
from app.modules.user.models import User

router = APIRouter(prefix="/api/v1/projects/{project_id}/tests", tags=["test"], dependencies=[Depends(require_project_access)])

@router.post("/suites", status_code=status.HTTP_201_CREATED)
async def create_suite(project_id: UUID, payload: SuiteCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    suite = tm.TestSuite(project_id=project_id, **payload.model_dump())
    db.add(suite)
    await db.commit()
    await db.refresh(suite)
    return {"id": suite.id, "name": suite.name}

@router.get("/suites", response_model=dict)
async def list_suites(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    rows = (await db.scalars(select(tm.TestSuite).where(tm.TestSuite.project_id == project_id))).all()
    return {"items": [{"id": r.id, "name": r.name} for r in rows], "meta": {"total": len(rows)}}

@router.post("/cases", status_code=status.HTTP_201_CREATED)
async def create_case(project_id: UUID, payload: CaseCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    case = tm.TestCase(**payload.model_dump())
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return {"id": case.id, "title": case.title}

@router.post("/plans", status_code=status.HTTP_201_CREATED)
async def create_plan(project_id: UUID, payload: PlanCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    plan = tm.TestPlan(project_id=project_id, name=payload.name, iteration_id=payload.iteration_id)
    db.add(plan)
    await db.flush()
    for order, case_id in enumerate(payload.case_ids):
        db.add(tm.TestPlanCase(plan_id=plan.id, case_id=case_id, order=order))
    await db.commit()
    return {"id": plan.id, "name": plan.name, "case_count": len(payload.case_ids)}
