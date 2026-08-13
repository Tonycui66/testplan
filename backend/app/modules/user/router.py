from __future__ import annotations
from datetime import timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError
from app.core.redis_client import get_redis
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.dependencies import bearer_scheme, get_current_user, get_db, require_superadmin
from app.modules.user.models import Team, TeamMember, User
from app.modules.user.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TeamCreate,
    TeamMemberCreate,
    TeamResponse,
    TeamUpdate,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/v1", tags=["iam"])


def user_to_response(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


async def issue_tokens(user: User) -> TokenResponse:
    settings = get_settings()
    access_token = create_token(str(user.id), timedelta(minutes=settings.access_token_expire_minutes), token_type="access")
    jti = str(uuid4())
    refresh_token = create_token(f"refresh:{user.id}", timedelta(days=settings.refresh_token_expire_days), token_type="refresh", jti=jti)
    redis = get_redis()
    await redis.set(f"refresh:{jti}", str(user.id), ex=settings.refresh_token_expire_days * 24 * 60 * 60)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user_to_response(user))


async def revoke_refresh_token(token: str) -> None:
    payload = decode_token(token)
    if payload is None or payload.get("type") != "refresh":
        return
    jti = payload.get("jti")
    if jti:
        await get_redis().delete(f"refresh:{jti}")


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    exists = await db.scalar(select(User).where(User.email == payload.email))
    if exists:
        raise ConflictError("Email already registered")
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        is_active=True,
        is_superadmin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await issue_tokens(user)


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    return await issue_tokens(user)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    token_payload = decode_token(payload.refresh_token)
    if token_payload is None or token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    subject = token_payload.get("sub")
    jti = token_payload.get("jti")
    if not isinstance(subject, str) or not subject.startswith("refresh:") or not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    exists = await get_redis().get(f"refresh:{jti}")
    if not exists:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    try:
        user_id = UUID(subject.removeprefix("refresh:"))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user = await db.get(User, user_id)
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    await revoke_refresh_token(payload.refresh_token)
    return await issue_tokens(user)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: Optional[LogoutRequest] = None,
    _: User = Depends(get_current_user),
) -> None:
    if payload is not None and payload.refresh_token:
        await revoke_refresh_token(payload.refresh_token)
    return None


@router.get("/auth/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return user_to_response(user)


@router.get("/teams", response_model=dict)
async def list_teams(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    offset = (max(page, 1) - 1) * min(max(page_size, 1), 100)
    stmt = (
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id, isouter=True)
        .where(or_(Team.created_by == user.id, TeamMember.user_id == user.id))
        .distinct()
    )
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    teams = (await db.scalars(stmt.order_by(Team.created_at.desc()).offset(offset).limit(page_size))).all()
    return {"items": [TeamResponse.model_validate(team).model_dump() for team in teams], "meta": {"page": page, "page_size": page_size, "total": total}}


@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(payload: TeamCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> TeamResponse:
    team = Team(name=payload.name, description=payload.description, created_by=user.id)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return TeamResponse.model_validate(team)


async def get_owned_team(team_id: UUID, user: User, db: AsyncSession) -> Team:
    team = await db.get(Team, team_id)
    if team is None:
        raise NotFoundError("Team not found")
    if team.created_by != user.id and not user.is_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team access denied")
    return team


@router.get("/teams/{team_id}", response_model=dict)
async def get_team(team_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    team = await get_owned_team(team_id, user, db)
    members = (await db.scalars(select(TeamMember).where(TeamMember.team_id == team_id))).all()
    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "members": [{"user_id": member.user_id, "role": member.role} for member in members],
    }


@router.patch("/teams/{team_id}", response_model=TeamResponse)
async def update_team(team_id: UUID, payload: TeamUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> TeamResponse:
    team = await get_owned_team(team_id, user, db)
    if payload.name is not None:
        team.name = payload.name
    if payload.description is not None:
        team.description = payload.description
    await db.commit()
    await db.refresh(team)
    return TeamResponse.model_validate(team)


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(team_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    team = await get_owned_team(team_id, user, db)
    await db.delete(team)
    await db.commit()


@router.post("/teams/{team_id}/members", response_model=TeamMemberCreate)
async def add_team_member(team_id: UUID, payload: TeamMemberCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> TeamMemberCreate:
    await get_owned_team(team_id, user, db)
    existing = await db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == payload.user_id))
    if existing:
        raise ConflictError("User is already a team member")
    member = TeamMember(team_id=team_id, user_id=payload.user_id, role=payload.role)
    db.add(member)
    await db.commit()
    return payload


@router.delete("/teams/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(team_id: UUID, user_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    await get_owned_team(team_id, user, db)
    member = await db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id))
    if member is None:
        raise NotFoundError("Team member not found")
    await db.delete(member)
    await db.commit()


@router.get("/admin/users", response_model=dict)
async def list_admin_users(
    page: int = 1,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_superadmin),
) -> Dict[str, Any]:
    stmt = select(User)
    if search:
        stmt = stmt.where(or_(User.email.ilike(f"%{search}%"), User.name.ilike(f"%{search}%")))
    offset = (max(page, 1) - 1) * 20
    users = (await db.scalars(stmt.order_by(User.created_at.desc()).offset(offset).limit(20))).all()
    return {"items": [user_to_response(user).model_dump() for user in users], "meta": {"page": page, "page_size": 20}}
