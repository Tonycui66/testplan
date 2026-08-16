from __future__ import annotations
from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, status
from datetime import datetime, timezone
from sqlalchemy import func, select
from app.core.pagination import normalize_pagination
from app.modules.deploy import models as deploy_models
from app.modules.project import models as project_models
from app.core.exceptions import ConflictError, NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db, require_project_access
from app.modules.test import models as tm
from app.modules.test.schemas import CaseCreate, CaseUpdate, PlanCreate, ResultCreate, RunCreate, SuiteCreate, SuiteUpdate
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

@router.patch("/suites/{suite_id}")
async def update_suite(project_id: UUID, suite_id: UUID, payload: SuiteUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    suite = await db.get(tm.TestSuite, suite_id)
    if suite is None or suite.project_id != project_id:
        raise NotFoundError("Test suite not found")
    if payload.name is not None:
        suite.name = payload.name
    if payload.description is not None:
        suite.description = payload.description
    await db.commit()
    return {"id": suite.id, "name": suite.name}


@router.delete("/suites/{suite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_suite(project_id: UUID, suite_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> None:
    suite = await db.get(tm.TestSuite, suite_id)
    if suite is None or suite.project_id != project_id:
        raise NotFoundError("Test suite not found")
    await db.delete(suite)
    await db.commit()


@router.get("/cases", response_model=dict)
async def list_cases(project_id: UUID, suite_id: UUID, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    suite = await db.get(tm.TestSuite, suite_id)
    if suite is None or suite.project_id != project_id:
        raise NotFoundError("Test suite not found")
    normalized_page, normalized_page_size = normalize_pagination(page, page_size)
    stmt = select(tm.TestCase).where(tm.TestCase.suite_id == suite_id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(tm.TestCase.created_at.desc()).offset((normalized_page - 1) * normalized_page_size).limit(normalized_page_size))).all()
    return {"items": [{"id": c.id, "title": c.title, "priority": c.priority, "type": c.type} for c in rows], "meta": {"page": normalized_page, "page_size": normalized_page_size, "total": total}}


@router.patch("/cases/{case_id}")
async def update_case(project_id: UUID, case_id: UUID, payload: CaseUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    case = await db.get(tm.TestCase, case_id)
    suite = await db.get(tm.TestSuite, case.suite_id) if case else None
    if case is None or suite is None or suite.project_id != project_id:
        raise NotFoundError("Test case not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(case, key, value)
    await db.commit()
    return {"id": case.id, "title": case.title}


@router.delete("/cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(project_id: UUID, case_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> None:
    case = await db.get(tm.TestCase, case_id)
    suite = await db.get(tm.TestSuite, case.suite_id) if case else None
    if case is None or suite is None or suite.project_id != project_id:
        raise NotFoundError("Test case not found")
    await db.delete(case)
    await db.commit()


@router.get("/plans", response_model=dict)
async def list_plans(project_id: UUID, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    normalized_page, normalized_page_size = normalize_pagination(page, page_size)
    stmt = select(tm.TestPlan).where(tm.TestPlan.project_id == project_id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(tm.TestPlan.created_at.desc()).offset((normalized_page - 1) * normalized_page_size).limit(normalized_page_size))).all()
    return {"items": [{"id": p.id, "name": p.name, "status": p.status} for p in rows], "meta": {"page": normalized_page, "page_size": normalized_page_size, "total": total}}


@router.post("/runs", status_code=status.HTTP_202_ACCEPTED)
async def create_run(project_id: UUID, payload: RunCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    plan = await db.get(tm.TestPlan, payload.plan_id)
    if plan is None or plan.project_id != project_id:
        raise NotFoundError("Test plan not found")
    if payload.environment_id is not None:
        environment = await db.get(deploy_models.Environment, payload.environment_id)
        if environment is None or environment.project_id != project_id:
            raise NotFoundError("Environment not found")
    run = tm.TestRun(plan_id=plan.id, environment_id=payload.environment_id, started_by=user.id, status="pending", started_at=datetime.now(timezone.utc))
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return {"id": run.id, "status": run.status}


@router.get("/runs/{run_id}")
async def get_run(project_id: UUID, run_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    run = await db.get(tm.TestRun, run_id)
    plan = await db.get(tm.TestPlan, run.plan_id) if run else None
    if run is None or plan is None or plan.project_id != project_id:
        raise NotFoundError("Test run not found")
    results = (await db.scalars(select(tm.TestRunResult).where(tm.TestRunResult.run_id == run.id))).all()
    return {"id": run.id, "status": run.status, "results": [{"case_id": r.case_id, "status": r.status} for r in results]}


@router.post("/runs/{run_id}/results", status_code=status.HTTP_201_CREATED)
async def submit_result(project_id: UUID, run_id: UUID, payload: ResultCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    run = await db.get(tm.TestRun, run_id)
    plan = await db.get(tm.TestPlan, run.plan_id) if run else None
    if run is None or plan is None or plan.project_id != project_id:
        raise NotFoundError("Test run not found")
    plan_case = await db.scalar(select(tm.TestPlanCase).where(tm.TestPlanCase.plan_id == plan.id, tm.TestPlanCase.case_id == payload.case_id))
    if plan_case is None:
        raise NotFoundError("Test case is not part of the plan")
    existing = await db.scalar(select(tm.TestRunResult).where(tm.TestRunResult.run_id == run.id, tm.TestRunResult.case_id == payload.case_id))
    if existing is not None:
        raise ConflictError("Test result already exists")
    result = tm.TestRunResult(run_id=run.id, case_id=payload.case_id, status=payload.status, comment=payload.comment, executed_by=user.id, executed_at=datetime.now(timezone.utc))
    db.add(result)
    await db.commit()
    return {"id": result.id, "status": result.status}
