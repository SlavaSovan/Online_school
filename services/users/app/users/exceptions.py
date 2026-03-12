from fastapi import HTTPException, status


class UserServiceError(Exception):
    """Базовое исключение для сервиса пользователей"""

    pass


class PermissionNotFoundError(UserServiceError):
    def __init__(self, permission_id: int = None, name: str = None):
        if permission_id:
            self.message = f"Permission with id {permission_id} not found"
        elif name:
            self.message = f"Permission with name '{name}' not found"
        else:
            self.message = "Permission not found"
        super().__init__(self.message)


class PermissionAlreadyExistsError(UserServiceError):
    def __init__(self, name: str):
        self.message = f"Permission with name '{name}' already exists"
        super().__init__(self.message)


class PermissionInUseError(UserServiceError):
    def __init__(self, permission_id: int):
        self.message = (
            f"Permission with id {permission_id} is used by roles and cannot be deleted"
        )
        super().__init__(self.message)


class RoleNotFoundError(UserServiceError):
    def __init__(self, role_id: int = None, name: str = None):
        if role_id:
            self.message = f"Role with id {role_id} not found"
        elif name:
            self.message = f"Role with name '{name}' not found"
        else:
            self.message = "Role not found"
        super().__init__(self.message)


class RoleAlreadyExistsError(UserServiceError):
    def __init__(self, name: str):
        self.message = f"Role with name '{name}' already exists"
        super().__init__(self.message)


class RoleHasUsersError(UserServiceError):
    def __init__(self, role_id: int, user_count: int):
        self.message = (
            f"Cannot delete role with {user_count} because it has {user_count} users"
        )
        super().__init__(self.message)


class DefaultRoleError(UserServiceError):
    def __init__(self, action: str = "delete"):
        self.message = f"Cannot {action} default role"
        super().__init__(self.message)


class UserNotFoundError(UserServiceError):
    def __init__(self, user_id: int = None, email: str = None):
        if user_id:
            self.message = f"User with id {user_id} not found"
        elif email:
            self.message = f"User with email '{email}' not found"
        else:
            self.message = "User not found"
        super().__init__(self.message)


class UserAlreadyExistsError(UserServiceError):
    def __init__(self, email: str = None):
        if email:
            self.message = f"User with email '{email}' already exists"
        else:
            self.message = "User already exists"
        super().__init__(self.message)


class UserInactiveError(UserServiceError):
    def __init__(self, user_id: int = None):
        if user_id:
            self.message = f"User with id {user_id} is inactive"
        else:
            self.message = "User account is inactive"
        super().__init__(self.message)


class PasswordMismatchError(UserServiceError):
    def __init__(self):
        self.message = "Passwords do not match"
        super().__init__(self.message)


class InvalidPasswordError(UserServiceError):
    def __init__(self):
        self.message = "Old password is incorrect"
        super().__init__(self.message)


class CannotDeleteSelfError(UserServiceError):
    def __init__(self):
        self.message = "You cannot delete your own account"
        super().__init__(self.message)


class CannotDeactivateSelfError(UserServiceError):
    def __init__(self):
        self.message = "You cannot deactivate your own account"
        super().__init__(self.message)
