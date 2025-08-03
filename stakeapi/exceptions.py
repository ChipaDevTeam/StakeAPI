"""Custom exceptions for StakeAPI."""


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


class NetworkError(StakeAPIError):
    """Raised when network requests fail."""
    pass


class GameNotFoundError(StakeAPIError):
    """Raised when a requested game is not found."""
    pass


class InsufficientFundsError(StakeAPIError):
    """Raised when user has insufficient funds for an operation."""
    pass
