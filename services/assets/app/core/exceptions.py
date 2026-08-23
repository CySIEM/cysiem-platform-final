"""Application-wide exception types, mapped to HTTP responses in
app/middleware/error_handler.py.
"""


class CySIEMException(Exception):
    """Base exception for all Layer 3 application errors."""

    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.detail
        super().__init__(self.detail)


class NotFoundError(CySIEMException):
    status_code = 404
    detail = "Resource not found"


class ValidationError(CySIEMException):
    status_code = 422
    detail = "Validation failed"


class DuplicateResourceError(CySIEMException):
    status_code = 409
    detail = "Resource already exists"


class IntegrationError(CySIEMException):
    status_code = 502
    detail = "Upstream integration error"


class AuthenticationError(CySIEMException):
    status_code = 401
    detail = "Authentication failed"


class AuthorizationError(CySIEMException):
    status_code = 403
    detail = "Not authorized to perform this action"
