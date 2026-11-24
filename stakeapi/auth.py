"""Authentication manager for StakeAPI."""

import json
import time
from typing import Any, Dict, List, Optional


class AuthManager:
    """Handles authentication for StakeAPI."""

    def __init__(
        self, access_token: Optional[str] = None, session_cookie: Optional[str] = None
    ):
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

    def set_access_token(
        self, access_token: str, expires_in: Optional[int] = None
    ) -> None:
        """
        Set access token.

        Args:
            access_token: Access token
            expires_in: Token expiration time in seconds
        """
        self.access_token = access_token
        if expires_in:
            self._token_expires_at = time.time() + expires_in

    def set_session_cookie(self, session_cookie: str) -> None:
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

    def clear_tokens(self) -> None:
        """Clear stored authentication tokens."""
        self.access_token = None
        self.session_cookie = None
        self._token_expires_at = None

    @staticmethod
    def parse_cookie_string(cookie_string: str) -> Dict[str, str]:
        """
        Parse a raw browser cookie string into a dictionary.

        Accepts the value of the Cookie header as copied from the browser's
        DevTools (Network tab → request → 'cookie' header), e.g.:
        "cf_clearance=abc; session=def; locale=en"

        A leading "Cookie:" prefix and line breaks are tolerated.

        Args:
            cookie_string: Raw cookie header string

        Returns:
            Dictionary mapping cookie names to values
        """
        # Collapse to a single line — files often contain stray newlines
        cookie_string = " ".join(
            line.strip() for line in cookie_string.splitlines()
        ).strip()
        if cookie_string.lower().startswith("cookie:"):
            cookie_string = cookie_string[len("cookie:") :].strip()

        cookies = {}
        for part in cookie_string.split(";"):
            part = part.strip()
            if not part or "=" not in part:
                continue
            name, _, value = part.partition("=")
            cookies[name.strip()] = value.strip()
        return cookies

    @staticmethod
    def load_cookie_file(path: str, domain: Optional[str] = None) -> str:
        """
        Load cookies from a file and return them as one Cookie header string.

        Two formats are accepted:

        - The raw Cookie header copied from the browser (e.g. cookie.txt):
          ``name1=value1; name2=value2``, optionally prefixed with ``Cookie:``.
        - A browser-extension JSON export (e.g. cookies.json): a list of
          objects with at least ``name`` and ``value``, plus optional
          ``domain`` and ``expirationDate``. A plain ``{"name": "value"}``
          object also works.

        Args:
            path: Path to the cookie file
            domain: For JSON exports, keep only cookies that apply to this
                host (e.g. "stake1017.com"). Expired cookies are always dropped.

        Returns:
            Cleaned cookie header string

        Raises:
            OSError: If the file cannot be read
            ValueError: If the file is empty, is malformed JSON, or has no
                usable cookies for ``domain``
        """
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        if raw.lstrip().startswith(("[", "{")):
            return AuthManager._cookie_header_from_json(raw, path, domain)

        cleaned = " ".join(line.strip() for line in raw.splitlines()).strip()
        if cleaned.lower().startswith("cookie:"):
            cleaned = cleaned[len("cookie:") :].strip()
        if not cleaned:
            raise ValueError(f"Cookie file {path!r} is empty")
        return cleaned

    @staticmethod
    def _cookie_header_from_json(raw: str, path: str, domain: Optional[str]) -> str:
        """Build a Cookie header from a JSON cookie export."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Cookie file {path!r} is not valid JSON: {e}")

        if isinstance(data, dict):
            entries: List[Dict[str, Any]] = [
                {"name": k, "value": v} for k, v in data.items()
            ]
        elif isinstance(data, list):
            entries = [c for c in data if isinstance(c, dict)]
        else:
            raise ValueError(
                f"Cookie file {path!r} must hold a list of cookies or a "
                "name → value object"
            )

        now = time.time()
        host = (domain or "").lower().lstrip(".")
        pairs: List[str] = []
        domains = set()
        for cookie in entries:
            name, value = cookie.get("name"), cookie.get("value")
            if not name or value is None:
                continue
            expires = cookie.get("expirationDate")
            if isinstance(expires, (int, float)) and expires < now:
                continue
            cookie_domain = str(cookie.get("domain") or "").lower().lstrip(".")
            if cookie_domain:
                domains.add(cookie_domain)
            if (
                host
                and cookie_domain
                and not (host == cookie_domain or host.endswith("." + cookie_domain))
            ):
                continue
            pairs.append(f"{name}={value}")

        if not pairs:
            if host and domains:
                raise ValueError(
                    f"Cookie file {path!r} has no unexpired cookies for {host!r} "
                    f"(it has cookies for: {', '.join(sorted(domains))}). Export "
                    "the cookies from the same domain you pass as base_url."
                )
            raise ValueError(f"Cookie file {path!r} has no usable cookies")
        return "; ".join(pairs)

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
        pattern = r"session=([^;]+)"
        match = re.search(pattern, curl_command)

        if match:
            return match.group(1).strip()

        return None
