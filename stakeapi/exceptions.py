"""Custom exceptions for StakeAPI."""

from typing import Any, Optional


class StakeAPIError(Exception):
    """Base exception for StakeAPI errors."""

    pass


class AuthenticationError(StakeAPIError):
    """Raised when authentication fails."""

    pass


class RateLimitError(StakeAPIError):
    """Raised when rate limit is exceeded."""

    pass


class ValidationError(StakeAPIError):
    """Raised when input validation fails."""

    pass


class GraphQLError(StakeAPIError):
    """Raised when the GraphQL API returns errors.

    Attributes:
        errors: The raw list of error objects returned by the API.
    """

    def __init__(self, message: str, errors: Optional[list[Any]] = None):
        super().__init__(message)
        self.errors: list[Any] = errors or []


class PermissionDeniedError(GraphQLError):
    """Raised when the API responds with a permission error.

    Usually means the access token / session cookie is invalid, expired,
    or belongs to a different stake domain (mirror) than the one being used.
    """

    pass


class NetworkError(StakeAPIError):
    """Raised when network requests fail."""

    pass


class GameNotFoundError(StakeAPIError):
    """Raised when a requested game is not found."""

    pass


class InsufficientFundsError(StakeAPIError):
    """Raised when user has insufficient funds for an operation."""

    pass
