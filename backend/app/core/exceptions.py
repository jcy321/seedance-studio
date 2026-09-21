from fastapi import status


class AppException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code


class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "未授权访问"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    def __init__(self, message: str = "无权限访问"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class ConflictException(AppException):
    def __init__(self, message: str = "资源冲突"):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)
