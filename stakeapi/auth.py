"""Authentication manager for StakeAPI."""

import hashlib
import hmac
import time
from typing import Dict, Optional
import base64
import json


class AuthManager:
    """Handles authentication for StakeAPI."""
    
    def __init__(self, access_token: Optional[str] = None, session_cookie: Optional[str] = None):
        """
        Initialize authentication manager.
        
        Args:
            access_token: Access token from stake.com (x-access-token)
            session_cookie: Session cookie for authentication
        """
        self.access_token = access_token
        self.session_cookie = session_cookie
        self._token_expires_at: Optional[float] = None
        
    async def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for requests.
        
        Returns:
            Dictionary of authentication headers
        """
        headers = {}
        
        if self.access_token:
            headers["X-Access-Token"] = self.access_token
            
        return headers
    
    def get_cookies(self) -> Dict[str, str]:
        """
        Get authentication cookies.
        
        Returns:
            Dictionary of cookies
        """
        cookies = {}
        
        if self.session_cookie:
            cookies["session"] = self.session_cookie
            
        return cookies
        
    def set_access_token(self, access_token: str, expires_in: Optional[int] = None):
        """
        Set access token.
        
        Args:
            access_token: Access token
            expires_in: Token expiration time in seconds
        """
        self.access_token = access_token
        if expires_in:
            self._token_expires_at = time.time() + expires_in
        
    def set_session_cookie(self, session_cookie: str):
        """
        Set session cookie.
        
        Args:
            session_cookie: Session cookie value
        """
        self.session_cookie = session_cookie
        
    def is_token_expired(self) -> bool:
        """
        Check if the current token is expired.
        
        Returns:
            True if token is expired or about to expire
        """
        if not self._token_expires_at:
            return False  # No expiration set, assume valid
            
        # Consider token expired 5 minutes before actual expiration
        return time.time() >= (self._token_expires_at - 300)
        
    def clear_tokens(self):
        """Clear stored authentication tokens."""
        self.access_token = None
        self.session_cookie = None
        self._token_expires_at = None
        
    @staticmethod
    def extract_access_token_from_curl(curl_command: str) -> Optional[str]:
        """
        Extract access token from curl command.
        
        Args:
            curl_command: Curl command string
            
        Returns:
            Extracted access token or None
        """
        import re
        
        # Look for x-access-token header
        pattern = r'-H\s+["\']x-access-token:\s*([^"\']+)["\']'
        match = re.search(pattern, curl_command, re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
            
        return None
        
    @staticmethod
    def extract_session_from_curl(curl_command: str) -> Optional[str]:
        """
        Extract session cookie from curl command.
        
        Args:
            curl_command: Curl command string
            
        Returns:
            Extracted session cookie or None
        """
        import re
        
        # Look for session cookie in -b parameter
        pattern = r'session=([^;]+)'
        match = re.search(pattern, curl_command)
        
        if match:
            return match.group(1).strip()
            
        return None
