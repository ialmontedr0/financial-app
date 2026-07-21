from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.infrastructure.models.permission import PermissionModel
from app.infrastructure.models.role import RoleModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

ALL_PERMISSIONS = [
    ("user:read", "user", "read", "Ver perfil de usuario"),
    ("user:write", "user", "write", "Editar perfil de usuario"),
    ("user:delete", "user", "delete", "Eliminar usuario"),
    ("user:list", "user", "list", "Listar todos los usuarios"),
    ("transaction:read", "transaction", "read", "Ver transacciones propias"),
    ("transaction:write", "transaction", "write", "Crear/editar transacciones"),
    ("transaction:delete", "transaction", "delete", "Eliminar transacciones"),
    ("transaction:list_all", "transaction", "list_all", "Ver todas las transacciones"),
    ("budget:read", "budget", "read", "Ver presupuestos"),
    ("budget:write", "budget", "write", "Crear/editar presupuestos"),
    ("budget:delete", "budget", "delete", "Eliminar presupuestos"),
    ("admin:users", "admin", "users", "Gestionar usuarios"),
    ("admin:roles", "admin", "roles", "Gestionar roles"),
    ("admin:permissions", "admin", "permissions", "Gestionar permisos"),
    ("admin:audit", "admin", "audit", "Ver logs de auditoria"),
    ("admin:settings", "admin", "settings", "Configurar sistema"),
    ("system:read", "system", "read", "Ver stats del sistema"),
    ("system:write", "system", "write", "Configurar sistema"),
]

DEFAULT_ROLES = {
    "user": {
        "display_name": "Usuario",
        "description": "Usuario regular del sistema",
        "is_system": True,
        "permissions": ["user:read", "user:write", "transaction:read", "transaction:write",
                        "transaction:delete", "budget:read", "budget:write", "budget:delete"],
        "parent": None,
    },
    "moderator": {
        "display_name": "Moderador",
        "description": "Moderador con permisos elevados",
        "is_system": True,
        "permissions": ["user:read", "user:list", "transaction:list_all", "admin:audit"],
        "parent": "user",
    },
    "admin": {
        "display_name": "Administrador",
        "description": "Administrador con todos los permisos",
        "is_system": True,
        "permissions": ["user:delete", "admin:users", "admin:roles", "admin:permissions",
                        "admin:settings", "system:write"],
        "parent": "moderator",
    },
}


async def seed_roles_and_permissions(db: AsyncSession) -> None:
    """Seed default roles and permissions."""
    # 1. Create permissions
    for name, resource, action, description in ALL_PERMISSIONS:
        existing = await db.execute(
            select(PermissionModel).where(PermissionModel.name == name)
        )
        if not existing.scalar_one_or_none():
            db.add(PermissionModel(
                name=name, resource=resource, action=action, description=description,
            ))
    await db.flush()

    # 2. Create roles (with parent hierarchy)
    role_cache: dict[str, RoleModel] = {}

    for role_name, config in DEFAULT_ROLES.items():
        existing = await db.execute(
            select(RoleModel).where(RoleModel.name == role_name)
        )
        role = existing.scalar_one_or_none()
        if not role:
            role = RoleModel(
                name=role_name,
                display_name=config["display_name"],
                description=config["description"],
                is_system=config["is_system"],
            )
            db.add(role)
            await db.flush()
        role_cache[role_name] = role

    # 3. Set parent roles
    for role_name, config in DEFAULT_ROLES.items():
        if config["parent"]:
            role = role_cache[role_name]
            parent = role_cache[config["parent"]]
            role.parent_role_id = parent.id
    await db.flush()

    # 4. Assign permissions to roles
    for role_name, config in DEFAULT_ROLES.items():
        role = role_cache[role_name]
        # Reload with permissions relationship loaded
        reloaded = await db.execute(
            select(RoleModel)
            .options(selectinload(RoleModel.permissions))
            .where(RoleModel.id == role.id)
        )
        role = reloaded.scalar_one()
        for perm_name in config["permissions"]:
            perm_result = await db.execute(
                select(PermissionModel).where(PermissionModel.name == perm_name)
            )
            perm = perm_result.scalar_one_or_none()
            if perm and perm not in role.permissions:
                role.permissions.append(perm)
        role_cache[role_name] = role
    await db.flush()
