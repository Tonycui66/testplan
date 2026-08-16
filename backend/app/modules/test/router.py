from __future__ import annotations
from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from app.core.pagination import normalize_pagination
from app.modules.project import models as project_models
from app.core.exceptions import NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db, require_project_access
from app.modules.test import models as tm
from app.modules.test.schemas import CaseCreate, PlanCreate, SuiteCreate
from app.modules.user.models import User

router = APIRouter(prefix="/api/v1/projects/{project_id}/tests", tags=["test"], dependencies=[Depends(require_project_access)])

@router.post("/suites", status_code=status.HTTP_201_CREATED)
async def create_suite(project_id: UUID, payload: SuiteCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    if payload.parent_id is not None:
        parent = await db.get(tm.TestSuite, payload.parent_id)
        if parent is None or parent.project_id != project_id:
            raise NotFoundError("Parent suite not found")
    suite = tm.TestSuite(project_id=project_id, **payload.model_dump())
    db.add(suite)
    await db.commit()
    await db.refresh(suite)
    return {"id": suite.id, "name": suite.name}

@router.get("/suites", response_model=dict)
async def list_suites(project_id: UUID, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    normalized_page, normalized_page_size = normalize_pagination(page, page_size)
    stmt = select(tm.TestSuite).where(tm.TestSuite.project_id == project_id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(tm.TestSuite.created_at.desc()).offset((normalized_page - 1) * normalized_page_size).limit(normalized_page_size))).all()
    return {"items": [{"id": r.id, "name": r.name} for r in rows], "meta": {"page": normalized_page, "page_size": normalized_page_size, "total": total}}

@router.post("/cases", status_code=status.HTTP_201_CREATED)
async def create_case(project_id: UUID, payload: CaseCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    suite = await db.get(tm.TestSuite, payload.suite_id)
    if suite is None or suite.project_id != project_id:
        raise NotFoundError("Test suite not found")
    case = tm.TestCase(**payload.model_dump())
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return {"id": case.id, "title": case.title}

@router.post("/plans", status_code=status.HTTP_201_CREATED)
async def create_plan(project_id: UUID, payload: PlanCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    if payload.iteration_id is not None:
        iteration = await db.get(project_models.Iteration, payload.iteration_id)
        if iteration is None or iteration.project_id != project_id:
            raise NotFoundError("Iteration not found")
    unique_case_ids = list(dict.fromkeys(payload.case_ids))
    if unique_case_ids:
        valid_cases = set((await db.scalars(select(tm.TestCase.id).join(tm.TestSuite, tm.TestCase.suite_id == tm.TestSuite.id).where(tm.TestSuite.project_id == project_id, tm.TestCase.id.in_(unique_case_ids)))).all())
        if valid_cases != set(unique_case_ids):
            raise NotFoundError("One or more test cases not found")
    plan = tm.TestPlan(project_id=project_id, name=payload.name, iteration_id=payload.iteration_id)
    db.add(plan)
    await db.flush()
    for order, case_id in enumerate(unique_case_ids):
        db.add(tm.TestPlanCase(plan_id=plan.id, case_id=case_id, order=order))
    await db.commit()
    return {"id": plan.id, "name": plan.name, "case_count": len(unique_case_ids)}
