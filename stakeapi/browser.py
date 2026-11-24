"""Drive a real Chrome window so the library works from a logged-in browser.

The site's bot protection accepts requests that come from a genuine browser
tab. ``BrowserSession`` opens Chrome (through chromedriver) at the login page,
waits while *you* log in, then sends the library's requests with ``fetch`` from
inside that page. Nothing is typed for you and no anti-detection tricks are
used: if the site refuses automated browsers, the requests are refused too.

Most people use it through ``StakeAPI.with_browser()``:

    async with StakeAPI.with_browser("https://stake1017.com") as client:
        print(await client.get_account_status())

Needs ``pip install "stakeapi[browser]"`` and Chrome. Selenium fetches a
matching chromedriver by itself the first time.

Command line (log in once, optionally save the cookies):

    python -m stakeapi.browser --base-url https://stake1017.com --out cookies.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlencode, urlparse

from .exceptions import AuthenticationError, NetworkError, StakeAPIError

# Opens the sign-in dialog of the site
LOGIN_PATH = "/?tab=login&modal=auth"

# The cookie that holds the login. Only this one is copied between browsers;
# the site's bot-protection cookies are tied to the browser that earned them.
LOGIN_COOKIE = "session"

# Headers the browser sets itself; fetch() silently ignores or forbids them
_FORBIDDEN_HEADERS = {
    "accept-encoding",
    "connection",
    "content-length",
    "cookie",
    "host",
    "origin",
    "referer",
    "user-agent",
}

# Runs inside the page; the last argument is the callback of execute_async_script
_FETCH_JS = """
const [method, url, headers, body, done] = arguments;
const init = {method: method, headers: headers, credentials: 'include'};
if (body !== null) { init.body = body; }
fetch(url, init).then(async (r) => {
  const text = await r.text();
  const h = {};
  r.headers.forEach((v, k) => { h[k] = v; });
  done({status: r.status, headers: h, text: text});
}).catch((e) => done({error: String(e)}));
"""


def default_profile_dir(base_url: str) -> Path:
    """Where the automation Chrome keeps its login between runs."""
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    host = urlparse(base_url).hostname or "site"
    return cache / "stakeapi" / f"chrome-profile-{host}"


class BrowserSession:
    """A Chrome window controlled through chromedriver."""

    def __init__(
        self,
        base_url: str,
        *,
        profile_dir: Optional[str] = None,
        headless: bool = False,
        chrome_binary: Optional[str] = None,
        chromedriver_path: Optional[str] = None,
        import_cookies_from: Optional[str] = None,
        chrome_profile: Optional[str] = None,
        window_size: Tuple[int, int] = (1100, 800),
        verbose: bool = True,
    ):
        """
        Args:
            base_url: The site or mirror, e.g. "https://stake1017.com"
            profile_dir: Folder for the Chrome profile. The login is kept
                there, so later runs need no login. Defaults to
                ~/.cache/stakeapi/chrome-profile-<host>.
            headless: Hide the window. You cannot log in by hand then, so use it
                only with an existing login or for public data.
            chrome_binary: Path to the Chrome executable, if not found
            chromedriver_path: Path to chromedriver. By default Selenium
                downloads one that matches your Chrome.
            import_cookies_from: "chrome", "chromium", "brave" or "edge": copy
                your login cookie from that browser on this computer instead of
                logging in by hand.
            chrome_profile: Profile of that browser, e.g. "Profile 2". By
                default the profile that is logged in to the site.
            verbose: Print short progress messages to stderr
        """
        self.base_url = base_url.rstrip("/")
        self.profile_dir = (
            Path(profile_dir) if profile_dir else default_profile_dir(base_url)
        )
        self.headless = headless
        self.chrome_binary = chrome_binary
        self.chromedriver_path = chromedriver_path
        self.import_cookies_from = import_cookies_from
        self.chrome_profile = chrome_profile
        self.window_size = window_size
        self.verbose = verbose
        self._driver: Any = None

    @property
    def started(self) -> bool:
        """True once the Chrome window is open."""
        return self._driver is not None

    def _say(self, message: str) -> None:
        if self.verbose:
            print(f"[stakeapi] {message}", file=sys.stderr, flush=True)

    def __enter__(self) -> "BrowserSession":
        self.start()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def start(self) -> None:
        """Open Chrome. Opens the login page when you are not logged in yet."""
        if self._driver is not None:
            return
        try:
            from selenium import webdriver
            from selenium.common.exceptions import WebDriverException
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
        except ImportError:
            raise StakeAPIError(
                'Browser login needs selenium: pip install "stakeapi[browser]"'
            )

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.profile_dir, 0o700)

        options = Options()
        options.add_argument(f"--user-data-dir={self.profile_dir}")
        options.add_argument(
            f"--window-size={self.window_size[0]},{self.window_size[1]}"
        )
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        if self.headless:
            options.add_argument("--headless=new")
        if self.chrome_binary:
            options.binary_location = self.chrome_binary
        service = (
            Service(executable_path=self.chromedriver_path)
            if self.chromedriver_path
            else Service()
        )

        self._say("Opening Chrome...")
        try:
            self._driver = webdriver.Chrome(service=service, options=options)
        except WebDriverException as e:
            raise StakeAPIError(
                f"Could not start Chrome: {getattr(e, 'msg', e)}. Is Chrome installed, "
                "and is the profile folder not already open in another Chrome window "
                f"({self.profile_dir})?"
            )

        self._driver.get(self.base_url + "/")
        if self.import_cookies_from and not self.is_logged_in():
            self._import_login_cookie()
        if not self.is_logged_in():
            self._driver.get(self.base_url + LOGIN_PATH)

    def _import_login_cookie(self) -> None:
        """Copy the login cookie from your normal browser into this window."""
        from selenium.common.exceptions import WebDriverException

        from .chrome_cookies import load_chrome_cookies

        host = urlparse(self.base_url).hostname or ""
        try:
            imported = load_chrome_cookies(
                host,
                browser=self.import_cookies_from or "chrome",
                profile=self.chrome_profile,
            )
        except StakeAPIError as e:
            self._say(f"Could not import cookies ({e}). Log in by hand instead.")
            return
        added = 0
        for c in imported.cookies:
            if c["name"] != LOGIN_COOKIE:
                continue
            cookie: Dict[str, Any] = {
                "name": c["name"],
                "value": c["value"],
                "path": c.get("path", "/"),
                "secure": c.get("secure", False),
            }
            if "expirationDate" in c:
                cookie["expiry"] = int(c["expirationDate"])
            try:
                self._driver.add_cookie(cookie)
                added += 1
            except WebDriverException:
                continue
        if added:
            self._say(
                f"Imported your login from {imported.browser} ({imported.profile})."
            )
            self._driver.refresh()
        else:
            self._say("No login cookie found in that browser. Log in by hand instead.")

    def close(self) -> None:
        """Close the Chrome window."""
        driver, self._driver = self._driver, None
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

    def _require_driver(self) -> Any:
        if self._driver is None:
            raise StakeAPIError("The browser is not open: call start() first")
        return self._driver

    def _check_alive(self) -> None:
        from selenium.common.exceptions import WebDriverException

        try:
            self._require_driver().title
        except WebDriverException:
            self._driver = None
            raise NetworkError("The Chrome window was closed.")

    def fetch(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> Tuple[int, Dict[str, str], str]:
        """
        Send a request with ``fetch`` from inside the page.

        Returns:
            (status, response headers, response text)

        Raises:
            NetworkError: The page could not send the request or the window is gone.
        """
        from selenium.common.exceptions import WebDriverException

        driver = self._require_driver()
        if params:
            url += ("&" if "?" in url else "?") + urlencode(params, doseq=True)

        safe_headers = {
            k: v
            for k, v in (headers or {}).items()
            if k.lower() not in _FORBIDDEN_HEADERS and not k.lower().startswith("sec-")
        }
        payload: Optional[str] = None
        if body is not None:
            payload = json.dumps(body)
            if not any(k.lower() == "content-type" for k in safe_headers):
                safe_headers["Content-Type"] = "application/json"

        try:
            if not (driver.current_url or "").startswith(self.base_url):
                driver.get(self.base_url + "/")
            driver.set_script_timeout(timeout)
            result = driver.execute_async_script(
                _FETCH_JS, method.upper(), url, safe_headers, payload
            )
        except WebDriverException as e:
            raise NetworkError(
                f"The browser could not send the request: {getattr(e, 'msg', e)}"
            )

        if not isinstance(result, dict) or "error" in result:
            error = result.get("error") if isinstance(result, dict) else result
            raise NetworkError(f"The browser could not reach {url}: {error}")
        return (
            int(result["status"]),
            dict(result.get("headers") or {}),
            str(result["text"]),
        )

    def is_logged_in(self) -> bool:
        """True if the page's session belongs to a logged-in user."""
        from selenium.common.exceptions import WebDriverException

        # The site's own client sends the login as an x-access-token header, so
        # the check has to as well: the cookie alone does not identify the user
        headers = {"X-Operation-Name": "UserId", "X-Operation-Type": "query"}
        try:
            cookie = self._require_driver().get_cookie(LOGIN_COOKIE)
            if cookie and cookie.get("value"):
                headers["X-Access-Token"] = cookie["value"]
            _, _, text = self.fetch(
                "POST",
                f"{self.base_url}/_api/graphql",
                body={
                    "query": "query UserId { user { id } }",
                    "operationName": "UserId",
                },
                headers=headers,
                timeout=15.0,
            )
            data = json.loads(text)
        except (StakeAPIError, WebDriverException, ValueError):
            return False
        user = (data.get("data") or {}).get("user") if isinstance(data, dict) else None
        return bool(user and user.get("id"))

    def wait_for_login(self, timeout: float = 300.0, poll: float = 2.0) -> None:
        """
        Wait until you have logged in to the site in the Chrome window.

        Returns at once when the window is already logged in.

        Raises:
            AuthenticationError: Not logged in within ``timeout`` seconds.
            NetworkError: The window was closed before logging in.
        """
        deadline = time.monotonic() + timeout
        announced = False
        while True:
            self._check_alive()
            if self.is_logged_in():
                if announced:
                    self._say("Logged in.")
                return
            if not announced:
                self._say(
                    f"Log in to {self.base_url} in the Chrome window "
                    f"(waiting up to {int(timeout)}s)."
                )
                announced = True
            if time.monotonic() >= deadline:
                raise AuthenticationError(
                    f"Not logged in after {int(timeout)}s. Log in in the Chrome "
                    "window and try again, or raise login_timeout."
                )
            time.sleep(poll)

    def cookies(self) -> List[Dict[str, Any]]:
        """The browser's cookies for the site, in the same shape as a JSON export."""
        out = []
        for c in self._require_driver().get_cookies():
            item = {
                "domain": c.get("domain", ""),
                "name": c["name"],
                "value": c["value"],
                "path": c.get("path", "/"),
                "secure": bool(c.get("secure")),
                "httpOnly": bool(c.get("httpOnly")),
            }
            if c.get("expiry"):
                item["expirationDate"] = float(c["expiry"])
            out.append(item)
        return out

    def cookie_header(self) -> str:
        """The cookies as a Cookie header string (name=value; ...)."""
        return "; ".join(f"{c['name']}={c['value']}" for c in self.cookies())

    def user_agent(self) -> str:
        """The User-Agent this Chrome sends."""
        return str(self._require_driver().execute_script("return navigator.userAgent"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m stakeapi.browser",
        description="Open Chrome at the site's login page, wait for you to log in, "
        "and optionally save the cookies.",
    )
    parser.add_argument("--base-url", default="https://stake.com")
    parser.add_argument("--profile-dir", help="Chrome profile folder (keeps the login)")
    parser.add_argument(
        "--import-from",
        choices=("chrome", "chromium", "brave", "edge"),
        help="copy your login from this browser instead of logging in by hand",
    )
    parser.add_argument("--chrome-profile", help='its profile, e.g. "Profile 2"')
    parser.add_argument(
        "--timeout", type=float, default=300.0, help="seconds to wait for login"
    )
    parser.add_argument("--out", help="save the cookies to this file (JSON, mode 0600)")
    args = parser.parse_args(argv)

    session = BrowserSession(
        args.base_url,
        profile_dir=args.profile_dir,
        import_cookies_from=args.import_from,
        chrome_profile=args.chrome_profile,
    )
    try:
        session.start()
        session.wait_for_login(args.timeout)
        print("Logged in.")
        if args.out:
            from .chrome_cookies import ImportedCookies, save_cookies

            cookies = session.cookies()
            save_cookies(
                args.out,
                ImportedCookies(cookies, "automation", "chrome", logged_in=True),
            )
            print(
                f"Saved {len(cookies)} cookies to {args.out}. "
                "It is a live login: keep it out of git."
            )
    except StakeAPIError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
