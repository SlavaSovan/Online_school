from functools import wraps
from typing import Callable, TypeVar, Any
from fastapi import HTTPException, status

from app.users.exceptions import (
    CannotDeactivateSelfError,
    CannotDeleteSelfError,
    InvalidPasswordError,
    PasswordMismatchError,
    PermissionNotFoundError,
    PermissionAlreadyExistsError,
    PermissionInUseError,
    RoleNotFoundError,
    RoleAlreadyExistsError,
    RoleHasUsersError,
    DefaultRoleError,
    UserAlreadyExistsError,
    UserInactiveError,
    UserNotFoundError,
    UserServiceError,
)

F = TypeVar("F", bound=Callable[..., Any])


def handle_user_errors(func: F):
    """Декоратор для обработки ошибок сервиса"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except PermissionNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except PermissionAlreadyExistsError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except PermissionInUseError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        except RoleNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except RoleAlreadyExistsError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except RoleHasUsersError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        except DefaultRoleError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except UserNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except UserAlreadyExistsError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except UserInactiveError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except PasswordMismatchError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except InvalidPasswordError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except CannotDeleteSelfError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except CannotDeactivateSelfError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except UserServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    return wrapper
