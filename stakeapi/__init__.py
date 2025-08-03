"""
StakeAPI - Unofficial Python API wrapper for stake.com

This package provides a comprehensive interface to interact with stake.com's
platform programmatically.
"""

from .client import StakeAPI
from .exceptions import StakeAPIError, AuthenticationError, RateLimitError
from ._version import __version__

__all__ = [
    "StakeAPI",
    "StakeAPIError", 
    "AuthenticationError",
    "RateLimitError",
    "__version__",
]
