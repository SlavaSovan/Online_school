from typing import List
from fastapi import APIRouter, Depends, Query, status

from app.auth.validation import get_current_active_auth_user
from app.core.dependencies import (
    get_permission_service,
    get_role_service,
    get_user_service_for_any_read,
    get_user_service_for_manage,
    get_permission_service,
)

from app.users.exception_handler import handle_user_errors
from app.users.models import User
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


permissions_router = APIRouter(prefix="/permissions", tags=["permissions"])
roles_router = APIRouter(prefix="/roles", tags=["roles"])
users_router = APIRouter(prefix="/users", tags=["users"])


# ================================= РАЗРЕШЕНИЯ =================================


@permissions_router.get("", response_model=List[PermissionResponse])
@handle_user_errors
async def get_permissions(
    permission_service: PermissionService = Depends(get_permission_service),
):
    permissions = await permission_service.get_all_permissions()
    return [PermissionResponse.model_validate(p) for p in permissions]


@permissions_router.post(
    "", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED
)
@handle_user_errors
async def create_permission(
    permission_data: PermissionCreate,
    permission_service: PermissionService = Depends(get_permission_service),
):
    permission = await permission_service.create_permission(permission_data)
    return PermissionResponse.model_validate(permission)


@permissions_router.get("/{permission_id}", response_model=PermissionResponse)
@handle_user_errors
async def get_permission(
    permission_id: int,
    permission_service: PermissionService = Depends(get_permission_service),
):
    permission = await permission_service.get_permission_by_id(permission_id)
    return PermissionResponse.model_validate(permission)


@permissions_router.patch("/{permission_id}", response_model=PermissionResponse)
@handle_user_errors
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    permission_service: PermissionService = Depends(get_permission_service),
):
    permission = await permission_service.update_permission(
        permission_id, permission_data
    )
    return PermissionResponse.model_validate(permission)


@permissions_router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_user_errors
async def delete_permission(
    permission_id: int,
    permission_service: PermissionService = Depends(get_permission_service),
):
    await permission_service.delete_permission(permission_id)


# ==================================== РОЛИ ====================================


@roles_router.get("", response_model=List[RoleResponse])
@handle_user_errors
async def get_roles(
    role_service: RoleService = Depends(get_role_service),
):
    roles_with_counts = await role_service.get_all_roles()

    result = []
    for role, user_count in roles_with_counts:
        role_response = RoleResponse.model_validate(role)
        role_response.user_count = user_count
        result.append(role_response)

    return result


@roles_router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
@handle_user_errors
async def create_role(
    role_data: RoleCreate,
    role_service: RoleService = Depends(get_role_service),
):
    role = await role_service.create_role(role_data)

    user_count = await role_service.repository.count_users_by_role(role.id)

    role_response = RoleResponse.model_validate(role)
    role_response.user_count = user_count

    return role_response


@roles_router.get("/{role_id}", response_model=RoleDetailResponse)
@handle_user_errors
async def get_role(
    role_id: int,
    role_service: RoleService = Depends(get_role_service),
):
    role, user_count, permissions = await role_service.get_role_by_id(role_id)

    role_response = RoleDetailResponse.model_validate(role)
    role_response.user_count = user_count
    role_response.permissions = [
        PermissionResponse.model_validate(p) for p in permissions
    ]

    return role_response


@roles_router.patch("/{role_id}", response_model=RoleResponse)
@handle_user_errors
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    role_service: RoleService = Depends(get_role_service),
):
    role = await role_service.update_role(role_id, role_data)

    user_count = await role_service.repository.count_users_by_role(role.id)

    role_response = RoleResponse.model_validate(role)
    role_response.user_count = user_count

    return role_response


@roles_router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_user_errors
async def delete_role(
    role_id: int,
    role_service: RoleService = Depends(get_role_service),
):
    await role_service.delete_role(role_id)


@roles_router.patch("/{role_id}/set-default", response_model=RoleResponse)
@handle_user_errors
async def set_default_role(
    role_id: int,
    role_service: RoleService = Depends(get_role_service),
):
    role = await role_service.set_default_role(role_id)

    user_count = await role_service.repository.count_users_by_role(role.id)

    role_response = RoleResponse.model_validate(role)
    role_response.user_count = user_count

    return role_response


@roles_router.put("/{role_id}/permissions", response_model=RoleDetailResponse)
@handle_user_errors
async def set_role_permissions(
    role_id: int,
    permission_ids: List[int],
    role_service: RoleService = Depends(get_role_service),
) -> RoleDetailResponse:
    role = await role_service.update_role_permissions(role_id, permission_ids)

    _, user_count, permissions = await role_service.get_role_by_id(role_id)

    role_response = RoleDetailResponse.model_validate(role)
    role_response.user_count = user_count
    role_response.permissions = [
        PermissionResponse.model_validate(p) for p in permissions
    ]
    return role_response


@roles_router.post(
    "/{role_id}/permissions/{permission_id}", response_model=RoleDetailResponse
)
@handle_user_errors
async def add_permission_to_role(
    role_id: int,
    permission_id: int,
    role_service: RoleService = Depends(get_role_service),
):
    role = await role_service.add_permission_to_role(role_id, permission_id)
    _, user_count, permissions = await role_service.get_role_by_id(role_id)

    role_response = RoleDetailResponse.model_validate(role)
    role_response.user_count = user_count
    role_response.permissions = [
        PermissionResponse.model_validate(p) for p in permissions
    ]
    return role_response


@roles_router.delete(
    "/{role_id}/permissions/{permission_id}", response_model=RoleDetailResponse
)
@handle_user_errors
async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    role_service: RoleService = Depends(get_role_service),
) -> RoleDetailResponse:
    role = await role_service.remove_permission_from_role(role_id, permission_id)
    _, user_count, permissions = await role_service.get_role_by_id(role_id)

    role_response = RoleDetailResponse.model_validate(role)
    role_response.user_count = user_count
    role_response.permissions = [
        PermissionResponse.model_validate(p) for p in permissions
    ]
    return role_response


# =============================== ОСНОВНЫЕ ПУТИ ================================


@users_router.get("", response_model=UserListResponse)
@handle_user_errors
async def get_all_users(
    skip: int = Query(0, ge=0, description="Skip N records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    include_inactive: bool = Query(False, description="Include inactive users"),
    user_service: UserService = Depends(get_user_service_for_any_read),
):
    users, total = await user_service.get_all_users(
        skip=skip, limit=limit, include_inactive=include_inactive
    )

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users], total=total
    )


@users_router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@handle_user_errors
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service_for_manage),
):
    user = await user_service.create_user(user_data)
    return UserResponse.model_validate(user)


@users_router.get("/stats", response_model=dict)
@handle_user_errors
async def get_user_stats(
    user_service: UserService = Depends(get_user_service_for_manage),
):
    return await user_service.get_stats()


@users_router.get("/roles/{role_id}", response_model=UserListResponse)
@handle_user_errors
async def get_users_by_role(
    role_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_inactive: bool = Query(False),
    user_service: UserService = Depends(get_user_service_for_any_read),
):
    users, total = await user_service.get_users_by_role(
        role_id, skip=skip, limit=limit, include_inactive=include_inactive
    )

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users], total=total
    )


@users_router.get("/{user_id}", response_model=UserDetailResponse)
@handle_user_errors
async def get_user(
    user_id: int,
    include_inactive: bool = Query(False),
    user_service: UserService = Depends(get_user_service_for_any_read),
):
    user = await user_service.get_user_by_id(user_id, include_inactive=include_inactive)
    return UserDetailResponse.model_validate(user)


@users_router.patch("/{user_id}", response_model=UserResponse)
@handle_user_errors
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_auth_user),
    user_service: UserService = Depends(get_user_service_for_manage),
):
    user_service.current_user = current_user
    user = await user_service.update_user(user_id, user_data)
    return UserResponse.model_validate(user)


@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_user_errors
async def delete_user(
    user_id: int,
    permanent: bool = Query(False),
    current_user: User = Depends(get_current_active_auth_user),
    user_service: UserService = Depends(get_user_service_for_manage),
):
    user_service.current_user = current_user
    await user_service.delete_user(user_id, permanent=permanent)


@users_router.patch("/{user_id}/activate", response_model=UserResponse)
@handle_user_errors
async def activate_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service_for_manage),
):
    user = await user_service.activate_user(user_id)
    return UserResponse.model_validate(user)


@users_router.patch("/{user_id}/deactivate", response_model=UserResponse)
@handle_user_errors
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_active_auth_user),
    user_service: UserService = Depends(get_user_service_for_manage),
):
    user_service.current_user = current_user
    user = await user_service.deactivate_user(user_id)
    return UserResponse.model_validate(user)


@users_router.patch("/{user_id}/role", response_model=UserResponse)
@handle_user_errors
async def change_user_role(
    user_id: int,
    request: ChangeRoleRequest,
    user_service: UserService = Depends(get_user_service_for_manage),
):
    user = await user_service.update_user(user_id, UserUpdate(role_id=request.role_id))
    return UserResponse.model_validate(user)
