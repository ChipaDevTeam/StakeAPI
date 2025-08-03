"""Authentication manager for StakeAPI."""

import hashlib
import hmac
import time
from typing import Dict, Optional
import base64
import json


class AuthManager:
    """Handles authentication for StakeAPI."""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize authentication manager.
        
        Args:
            api_key: API key from stake.com
            api_secret: API secret from stake.com
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        
    async def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for requests.
        
        Returns:
            Dictionary of authentication headers
        """
        headers = {}
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
            
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
            
        return headers
        
    def generate_signature(self, method: str, endpoint: str, body: str = "") -> str:
        """
        Generate HMAC signature for authenticated requests.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            body: Request body
            
        Returns:
            HMAC signature
        """
        if not self.api_secret:
            return ""
            
        timestamp = str(int(time.time()))
        message = f"{timestamp}{method.upper()}{endpoint}{body}"
        
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
        
    def set_tokens(self, access_token: str, refresh_token: str, expires_in: int):
        """
        Set authentication tokens.
        
        Args:
            access_token: Access token
            refresh_token: Refresh token
            expires_in: Token expiration time in seconds
        """
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expires_at = time.time() + expires_in
        
    def is_token_expired(self) -> bool:
        """
        Check if the current token is expired.
        
        Returns:
            True if token is expired or about to expire
        """
        if not self._token_expires_at:
            return True
            
        # Consider token expired 5 minutes before actual expiration
        return time.time() >= (self._token_expires_at - 300)
        
    def clear_tokens(self):
        """Clear stored authentication tokens."""
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = None
