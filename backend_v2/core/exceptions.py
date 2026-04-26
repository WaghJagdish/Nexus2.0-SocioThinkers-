from typing import Any, Optional
from enum import Enum
import http
from dataclasses import dataclass


class ErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    TRANSCRIPTION_FAILED = "TRANSCRIPTION_FAILED"
    SYNTHESIS_FAILED = "SYNTHESIS_FAILED"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    AGENT_ERROR = "AGENT_ERROR"
    AUTH_FAILED = "AUTH_FAILED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"


@dataclass
class ErrorResponse:
    code: ErrorCode
    message: str
    details: Optional[dict[str, Any]] = None
    status_code: int = 500
    request_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details or {},
                "request_id": self.request_id,
            }
        }


class ApplicationException(Exception):
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(ApplicationException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=400,
            details=details,
        )


class AuthenticationException(ApplicationException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            error_code=ErrorCode.AUTH_FAILED,
            message=message,
            status_code=401,
        )


class RateLimitException(ApplicationException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            status_code=429,
        )


class ResourceNotFoundException(ApplicationException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=f"{resource} with id '{resource_id}' not found",
            status_code=404,
        )


class ExternalServiceException(ApplicationException):
    def __init__(self, service_name: str, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.EXTERNAL_API_ERROR,
            message=f"{service_name} error: {message}",
            status_code=503,
            details=details,
        )


class TranscriptionException(ApplicationException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.TRANSCRIPTION_FAILED,
            message=message,
            status_code=503,
            details=details,
        )


class SynthesisException(ApplicationException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.SYNTHESIS_FAILED,
            message=message,
            status_code=503,
            details=details,
        )


class AgentException(ApplicationException):
    def __init__(self, agent_id: str, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.AGENT_ERROR,
            message=f"Agent '{agent_id}' error: {message}",
            status_code=500,
            details=details,
        )


class DatabaseException(ApplicationException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            message=message,
            status_code=503,
            details=details,
        )


class TimeoutException(ApplicationException):
    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            error_code=ErrorCode.TIMEOUT,
            message=f"Operation '{operation}' timed out after {timeout_seconds}s",
            status_code=504,
        )
