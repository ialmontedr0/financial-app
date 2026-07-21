from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.api.v1.admin import schemas as admin_schemas
from app.audit.service import AuditService
from app.infrastructure.repositories.audit_repository import AuditRepository
from app.infrastructure.repositories.permission_repository import PermissionRepository
from app.infrastructure.repositories.role_repository import RoleRepository
from app.infrastructure.repositories.user_repository import UserRepository

router = APIRouter(prefix="/admin", tags=["Admin"])


# ─── Roles ──────────────────────────────────────────────

@router.get("/roles", response_model=admin_schemas.RoleListResponse)
async def list_roles(
    include_inactive: bool = Query(False),
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    repo = RoleRepository(db)
    roles = await repo.list_all(include_inactive=include_inactive)
    return admin_schemas.RoleListResponse(roles=roles, total=len(roles))


@router.post("/roles", response_model=admin_schemas.RoleResponse, status_code=201)
async def create_role(
    body: admin_schemas.RoleCreate,
    request: Request,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    repo = RoleRepository(db)
    existing = await repo.get_by_name(body.name)
    if existing:
        raise HTTPException(status_code=409, detail="Role already exists")

    role = await repo.create(
        name=body.name,
        display_name=body.display_name,
        description=body.description,
        parent_role_id=body.parent_role_id,
    )

    audit = AuditService(db)
    await audit.log_action(
        user_id=UUID(current_user["sub"]),
        action="create",
        resource="role",
        resource_id=role.id,
        details={"name": role.name},
        ip_address=request.client.host if request.client else None,
    )

    return role


@router.get("/roles/{role_id}", response_model=admin_schemas.RoleResponse)
async def get_role(
    role_id: UUID,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    repo = RoleRepository(db)
    role = await repo.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.put("/roles/{role_id}", response_model=admin_schemas.RoleResponse)
async def update_role(
    role_id: UUID,
    body: admin_schemas.RoleUpdate,
    request: Request,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    repo = RoleRepository(db)
    role = await repo.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    data = body.model_dump(exclude_unset=True)
    role = await repo.update(role, **data)

    audit = AuditService(db)
    await audit.log_action(
        user_id=UUID(current_user["sub"]),
        action="update",
        resource="role",
        resource_id=role.id,
        details=data,
        ip_address=request.client.host if request.client else None,
    )

    return role


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: UUID,
    request: Request,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    repo = RoleRepository(db)
    role = await repo.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system role")

    ok = await repo.delete(role_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Cannot delete role")

    audit = AuditService(db)
    await audit.log_action(
        user_id=UUID(current_user["sub"]),
        action="delete",
        resource="role",
        resource_id=role_id,
        details={"name": role.name},
        ip_address=request.client.host if request.client else None,
    )

    return {"success": True, "message": f"Role '{role.name}' deleted"}


@router.post("/roles/{role_id}/permissions")
async def assign_permission(
    role_id: UUID,
    body: admin_schemas.AssignPermissionRequest,
    request: Request,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    repo = RoleRepository(db)
    role = await repo.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    ok = await repo.assign_permission(role_id, body.permission_id)
    if not ok:
        raise HTTPException(status_code=409, detail="Permission already assigned")

    audit = AuditService(db)
    await audit.log_action(
        user_id=UUID(current_user["sub"]),
        action="assign_permission",
        resource="role",
        resource_id=role_id,
        details={"permission_id": str(body.permission_id)},
        ip_address=request.client.host if request.client else None,
    )

    return {"success": True}


@router.delete("/roles/{role_id}/permissions/{permission_id}")
async def remove_permission(
    role_id: UUID,
    permission_id: UUID,
    request: Request,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    repo = RoleRepository(db)
    ok = await repo.remove_permission(role_id, permission_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Permission not assigned")

    audit = AuditService(db)
    await audit.log_action(
        user_id=UUID(current_user["sub"]),
        action="remove_permission",
        resource="role",
        resource_id=role_id,
        details={"permission_id": str(permission_id)},
        ip_address=request.client.host if request.client else None,
    )

    return {"success": True}


# ─── Permisos ──────────────────────────────────────────

@router.get("/permissions", response_model=admin_schemas.PermissionListResponse)
async def list_permissions(
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    repo = PermissionRepository(db)
    perms = await repo.list_all()
    return admin_schemas.PermissionListResponse(permissions=perms, total=len(perms))


@router.get("/permissions/{permission_id}", response_model=admin_schemas.PermissionResponse)
async def get_permission(
    permission_id: UUID,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    repo = PermissionRepository(db)
    perm = await repo.get_by_id(permission_id)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    return perm


# ─── User Management ───────────────────────────────────

@router.get("/users", response_model=admin_schemas.UserListAdminResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: str | None = Query(None),
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    users = await user_repo.list_users(skip=skip, limit=limit, role=role)
    total = await user_repo.count_users(role=role)
    items = [
        admin_schemas.UserListResponse(
            id=u.id, email=u.email, role=u.role,
            is_active=u.is_active, is_verified=u.is_verified,
            created_at=u.created_at,
        )
        for u in users
    ]
    return admin_schemas.UserListAdminResponse(users=items, total=total)


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    body: admin_schemas.UserRoleUpdateRequest,
    request: Request,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    role_repo = RoleRepository(db)
    role = await role_repo.get_by_name(body.role)
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{body.role}' not found")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role
    user.role = body.role
    await db.flush()

    audit = AuditService(db)
    await audit.log_action(
        user_id=UUID(current_user["sub"]),
        action="change_role",
        resource="user",
        resource_id=user_id,
        details={"old_role": old_role, "new_role": body.role},
        ip_address=request.client.host if request.client else None,
    )

    return {"success": True, "old_role": old_role, "new_role": body.role}


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: UUID,
    body: admin_schemas.UserStatusUpdateRequest,
    request: Request,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_status = user.is_active
    user.is_active = body.is_active
    await db.flush()

    audit = AuditService(db)
    await audit.log_action(
        user_id=UUID(current_user["sub"]),
        action="toggle_active",
        resource="user",
        resource_id=user_id,
        details={"old_active": old_status, "new_active": body.is_active},
        ip_address=request.client.host if request.client else None,
    )

    return {"success": True, "is_active": body.is_active}


# ─── Audit Log ─────────────────────────────────────────

@router.get("/audit", response_model=admin_schemas.AuditLogListResponse)
async def list_audit_logs(
    user_id: UUID | None = Query(None),
    action: str | None = Query(None),
    resource: str | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    repo = AuditRepository(db)
    logs = await repo.list_logs(
        user_id=user_id, action=action, resource=resource,
        status=status, skip=skip, limit=limit,
    )
    total = await repo.count_logs(user_id=user_id, action=action, resource=resource)
    return admin_schemas.AuditLogListResponse(logs=logs, total=total)


@router.get("/audit/stats", response_model=admin_schemas.AuditLogStatsResponse)
async def audit_stats(
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    repo = AuditRepository(db)
    return await repo.stats()


@router.get("/audit/{log_id}", response_model=admin_schemas.AuditLogResponse)
async def get_audit_log(
    log_id: UUID,
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    repo = AuditRepository(db)
    log = await repo.get_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log


# ─── System Stats ──────────────────────────────────────

@router.get("/stats", response_model=admin_schemas.SystemStatsResponse)
async def system_stats(
    current_user: dict = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import func, select

    from app.infrastructure.models.permission import PermissionModel
    from app.infrastructure.models.role import RoleModel
    from app.infrastructure.models.system_audit_log import SystemAuditLogModel
    from app.infrastructure.models.user import UserModel
    from app.infrastructure.models.user_session import UserSessionModel

    users_total = (await db.execute(select(func.count(UserModel.id)))).scalar() or 0
    users_active = (await db.execute(
        select(func.count(UserModel.id)).where(UserModel.is_active == True)  # noqa: E712
    )).scalar() or 0
    roles_total = (await db.execute(select(func.count(RoleModel.id)))).scalar() or 0
    perms_total = (await db.execute(select(func.count(PermissionModel.id)))).scalar() or 0
    audit_total = (await db.execute(select(func.count(SystemAuditLogModel.id)))).scalar() or 0
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_logins = (await db.execute(
        select(func.count(UserSessionModel.id)).where(UserSessionModel.created_at >= week_ago)
    )).scalar() or 0

    return admin_schemas.SystemStatsResponse(
        total_users=users_total,
        active_users=users_active,
        total_roles=roles_total,
        total_permissions=perms_total,
        total_audit_entries=audit_total,
        recent_logins=recent_logins,
    )
