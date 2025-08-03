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

from .client import StakeAPI
from .exceptions import StakeAPIError, AuthenticationError, RateLimitError
from .auth import AuthManager
from ._version import __version__

__all__ = [
    "StakeAPI",
    "AuthManager",
    "StakeAPIError", 
    "AuthenticationError",
    "RateLimitError",
    "__version__",
]
