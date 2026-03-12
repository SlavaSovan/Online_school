from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import List, Optional


class PermissionBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None
    category: str


class PermissionCreate(PermissionBase):
    @field_validator("name")
    def validate_name(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Permission name cannot be empty")
        if " " in v:
            raise ValueError("Permission name cannot contain spaces")
        if not all(c.isalnum() or c in [":", "_", "-"] for c in v):
            raise ValueError(
                "Permission name can only contain alphanumeric characters, colons, underscores and hyphens"
            )
        return v

    @field_validator("category")
    def validate_category(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Category cannot be empty")
        return v


class PermissionUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None

    @field_validator("category")
    def validate_category(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Category cannot be empty")
        return v


class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None
    is_default: bool = False


class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = None


class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    user_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class RoleDetailResponse(RoleResponse):
    permissions: Optional[List[PermissionResponse]]


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    patronymic: Optional[str] = Field(None, max_length=50)


class UserRegister(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    password_confirm: str = Field(..., min_length=6, max_length=100)


class UserCreate(UserRegister):
    role_id: Optional[int] = None
    password: str = Field(..., min_length=6, max_length=100)
    password_confirm: str = Field(..., min_length=6, max_length=100)


class UserUpdateProfile(UserBase):
    email: Optional[EmailStr] = None


class UserUpdate(UserUpdateProfile):
    is_active: Optional[bool] = None
    role_id: Optional[int] = None


class ChangeRoleRequest(BaseModel):
    role_id: int


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    patronymic: Optional[str]
    is_active: bool
    role_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(UserResponse):
    role: Optional[RoleResponse]

    @field_validator("role", mode="before")
    @classmethod
    def prepare_role_for_validation(cls, v):
        if v is None:
            return None

        if hasattr(v, "id"):
            return {
                "id": v.id,
                "name": v.name,
                "description": v.description,
                "is_default": v.is_default,
                "created_at": v.created_at,
            }
        return v


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int


class PasswordChange(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=100)
    new_password_confirm: str = Field(..., min_length=6, max_length=100)
