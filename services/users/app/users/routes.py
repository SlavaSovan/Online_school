from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    get_permission_service,
    get_role_service,
    get_user_service_for_any_edit,
    get_user_service_for_any_read,
    get_user_service_for_manage,
    get_permission_service,
)

from app.users.services import PermissionService, RoleService, UserService
from app.users.schemas import (
    ChangeRoleRequest,
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    RoleCreate,
    RoleDetailResponse,
    RoleResponse,
    RoleUpdate,
    UserCreate,
    UserDetailResponse,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

users_router = APIRouter(prefix="/users", tags=["users"])
roles_router = APIRouter(prefix="/roles", tags=["roles"])
permissions_router = APIRouter(prefix="/permissions", tags=["permissions"])
permissions_manager_router = APIRouter(prefix="/manager", tags=["manager"])


# ==================================== РОЛИ ====================================


@roles_router.get("/all", response_model=List[RoleResponse])
async def get_roles(
    role_service: RoleService = Depends(get_role_service),
):
    return await role_service.get_all_roles()


@roles_router.post("/create", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    role_service: RoleService = Depends(get_role_service),
):
    return await role_service.create_role(role_data)


@roles_router.get("/{role_id}", response_model=RoleDetailResponse)
async def get_role(
    role_id: int,
    role_service: RoleService = Depends(get_role_service),
):
    return await role_service.get_role_by_id(role_id)


@roles_router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    role_service: RoleService = Depends(get_role_service),
):
    return await role_service.update_role(role_id, role_data)


@roles_router.put("/{role_id}/set-default", response_model=RoleResponse)
async def set_default_role(
    role_id: int,
    role_service: RoleService = Depends(get_role_service),
):
    return await role_service.set_default_role(role_id)


@roles_router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    role_service: RoleService = Depends(get_role_service),
):
    success = await role_service.delete_role(role_id)
    if success:
        return {"message": "Role deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )


# ================================= РАЗРЕШЕНИЯ =================================


@permissions_router.get("/all", response_model=List[PermissionResponse])
async def get_permissions(
    category: Optional[str] = None,
    permission_service: PermissionService = Depends(get_permission_service),
):
    if category:
        return await permission_service.get_permissions_by_category(category)
    return await permission_service.get_all_permissions()


@permissions_router.post("/create", response_model=PermissionResponse)
async def create_permission(
    permission_data: PermissionCreate,
    permission_service: PermissionService = Depends(get_permission_service),
):
    return await permission_service.create_permission(permission_data)


@permissions_router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: int,
    permission_service: PermissionService = Depends(get_permission_service),
):
    return await permission_service.get_permission_by_id(permission_id)


@permissions_router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    permission_service: PermissionService = Depends(get_permission_service),
):
    return await permission_service.update_permission(permission_id, permission_data)


@permissions_router.delete("/{permission_id}")
async def delete_permission(
    permission_id: int,
    permission_service: PermissionService = Depends(get_permission_service),
):
    success = await permission_service.delete_permission(permission_id)
    if success:
        return {"message": "Permission deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found"
        )


@permissions_router.get("/categories", response_model=List[str])
async def get_permission_categories(
    permission_service: PermissionService = Depends(get_permission_service),
):
    permissions = await permission_service.get_all_permissions()
    categories = sorted(set(p.category for p in permissions))
    return categories


# ======================== УПРАВЛЕНИЕ РАЗРЕШЕНИЯМИ РОЛИ ========================


@permissions_manager_router.put(
    "/{role_id}/{permission_id}", response_model=RoleDetailResponse
)
async def add_permission_to_role(
    role_id: int,
    permission_id: int,
    role_service: RoleService = Depends(get_role_service),
):
    return await role_service.add_permission_to_role(role_id, permission_id)


@permissions_manager_router.delete(
    "/{role_id}/{permission_id}", response_model=RoleDetailResponse
)
async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    role_service: RoleService = Depends(get_role_service),
) -> RoleDetailResponse:
    return await role_service.remove_permission_from_role(role_id, permission_id)


@permissions_manager_router.put("/{role_id}", response_model=RoleDetailResponse)
async def set_role_permissions(
    role_id: int,
    permission_ids: List[int],
    role_service: RoleService = Depends(get_role_service),
) -> RoleDetailResponse:
    return await role_service.update_role_permissions(role_id, permission_ids)


# =============================== ОСНОВНЫЕ ПУТИ ================================


@users_router.get("/all", response_model=UserListResponse)
async def get_all_users(
    user_service: UserService = Depends(get_user_service_for_any_read),
):
    return await user_service.get_all_users()


@users_router.post("/create", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service_for_manage),
):
    return await user_service.create_user(user_data)


@users_router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service_for_any_read),
):
    return await user_service.get_user_by_id(user_id)


@users_router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service_for_any_edit),
):
    return await user_service.update_user(user_id, user_data)


@users_router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service_for_manage),
):
    success = await user_service.delete_user(user_id)
    if success:
        return {"message": "User deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@users_router.put("/{user_id}/activate")
async def activate_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service_for_manage),
):
    user = await user_service.update_user(user_id, UserUpdate(is_active=True))
    return {"message": "User activated", "user": user}


@users_router.put("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service_for_manage),
):
    user = await user_service.update_user(user_id, UserUpdate(is_active=False))
    return {"message": "User deactivated", "user": user}


@users_router.put("/{user_id}/role")
async def change_user_role(
    user_id: int,
    request: ChangeRoleRequest,
    user_service: UserService = Depends(get_user_service_for_manage),
):
    user = await user_service.update_user(user_id, UserUpdate(role_id=request.role_id))
    return {"message": "User role updated", "user": user}
