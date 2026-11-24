"""
StakeAPI - Unofficial Python API wrapper for stake.com

This package provides a comprehensive interface to interact with stake.com's
GraphQL API programmatically.

Example usage:
    import asyncio
    from stakeapi import StakeAPI

    async def main():
        async with StakeAPI(access_token="your_token") as client:
            balance = await client.get_user_balance()
            print(balance)

    asyncio.run(main())
"""

from ._version import __version__
from .auth import AuthManager
from .client import StakeAPI
from .exceptions import (
    AuthenticationError,
    BettingDisabledError,
    GraphQLError,
    NetworkError,
    PermissionDeniedError,
    RateLimitError,
    StakeAPIError,
    ValidationError,
)
from .websocket import StakeWebSocket

__all__ = [
    "StakeAPI",
    "StakeWebSocket",
    "AuthManager",
    "StakeAPIError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NetworkError",
    "GraphQLError",
    "PermissionDeniedError",
    "BettingDisabledError",
    "__version__",
]
