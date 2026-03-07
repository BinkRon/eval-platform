"""Domain exceptions for the eval platform.

Service layer raises these instead of HTTPException.
Global exception handlers in main.py convert them to HTTP responses.
"""


class DomainError(Exception):
    """Base class for all domain exceptions."""
    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""
    pass


class ValidationError(DomainError):
    """Raised when a business rule or precondition is violated."""
    pass


class ConflictError(DomainError):
    """Raised when an operation conflicts with current state."""
    pass
