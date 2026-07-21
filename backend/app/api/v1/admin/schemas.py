from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class RoleResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: str | None = None
    parent_role_id: UUID | None = None
    is_system: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str
    display_name: str
    description: str | None = None
    parent_role_id: UUID | None = None


class RoleUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class RoleListResponse(BaseModel):
    roles: list[RoleResponse]
    total: int


class PermissionResponse(BaseModel):
    id: UUID
    name: str
    resource: str
    action: str
    description: str | None = None

    model_config = {"from_attributes": True}


class PermissionListResponse(BaseModel):
    permissions: list[PermissionResponse]
    total: int


class AssignPermissionRequest(BaseModel):
    permission_id: UUID


class UserListResponse(BaseModel):
    id: UUID
    email: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListAdminResponse(BaseModel):
    users: list[UserListResponse]
    total: int


class UserRoleUpdateRequest(BaseModel):
    role: str


class UserStatusUpdateRequest(BaseModel):
    is_active: bool


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None = None
    action: str
    resource: str
    resource_id: UUID | None = None
    details: dict[str, Any] | None = None
    ip_address: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogResponse]
    total: int


class AuditLogStatsResponse(BaseModel):
    total: int
    by_action: dict[str, int]
    by_resource: dict[str, int]
    by_status: dict[str, int]


class SystemStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_roles: int
    total_permissions: int
    total_audit_entries: int
    recent_logins: int
