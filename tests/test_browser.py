"""Tests for the browser session and the client's browser transport (no real Chrome)."""

import json
import sys

import pytest
from selenium.common.exceptions import WebDriverException

from stakeapi import StakeAPI, chrome_cookies
from stakeapi.browser import BrowserSession, default_profile_dir
from stakeapi.chrome_cookies import ImportedCookies
from stakeapi.exceptions import (
    AuthenticationError,
    NetworkError,
    StakeAPIError,
    ValidationError,
)

BASE = "https://stake1017.com"
LOGGED_IN = {"status": 200, "headers": {}, "text": '{"data":{"user":{"id":"u1"}}}'}
LOGGED_OUT = {"status": 200, "headers": {}, "text": '{"data":{"user":null}}'}


class FakeDriver:
    """Just enough of selenium's Chrome driver."""

    def __init__(self, replies=(), url=BASE + "/"):
        self.replies = list(replies)
        self.current_url = url
        self.calls = []
        self.visited = []
        self.added = []
        self.refreshed = False
        self.closed = False
        self.alive = True
        self.cookie_list = [
            {"name": "session", "value": "tok", "domain": "stake1017.com",
             "path": "/", "secure": True, "httpOnly": False, "expiry": 2000000000},
            {"name": "locale", "value": "en", "domain": ".stake1017.com"},
        ]  # fmt: skip

    @property
    def title(self):
        if not self.alive:
            raise WebDriverException("window closed")
        return "title"

    def get(self, url):
        self.visited.append(url)
        self.current_url = url

    def set_script_timeout(self, seconds):
        self.timeout = seconds

    def execute_async_script(self, script, *args):
        self.calls.append(args)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    def execute_script(self, script):
        return "Mozilla/5.0 Test"

    def get_cookies(self):
        return self.cookie_list

    def get_cookie(self, name):
        return next((c for c in self.cookie_list if c["name"] == name), None)

    def add_cookie(self, cookie):
        self.added.append(cookie)

    def refresh(self):
        self.refreshed = True

    def quit(self):
        self.closed = True


def session_with(*replies, **driver_kwargs):
    session = BrowserSession(BASE, verbose=False)
    session._driver = FakeDriver(replies, **driver_kwargs)
    return session


def test_fetch_builds_the_request_for_the_page():
    session = session_with({"status": 200, "headers": {"x": "1"}, "text": "ok"})
    status, headers, text = session.fetch(
        "post",
        BASE + "/_api/graphql",
        params={"a": 1},
        body={"query": "q"},
        headers={
            "X-Operation-Name": "Op",
            "Cookie": "no",
            "User-Agent": "no",
            "Sec-Fetch-Mode": "no",
        },
    )
    assert (status, headers, text) == (200, {"x": "1"}, "ok")
    method, url, sent_headers, body = session._driver.calls[0]
    assert method == "POST" and url == BASE + "/_api/graphql?a=1"
    assert sent_headers == {
        "X-Operation-Name": "Op",
        "Content-Type": "application/json",
    }
    assert json.loads(body) == {"query": "q"}


def test_fetch_goes_back_to_the_site_when_on_another_page():
    session = session_with(
        {"status": 200, "headers": {}, "text": "{}"}, url="about:blank"
    )
    session.fetch("GET", BASE + "/x")
    assert session._driver.visited == [BASE + "/"]


def test_fetch_errors_become_network_errors():
    with pytest.raises(NetworkError, match="Failed to fetch"):
        session_with({"error": "TypeError: Failed to fetch"}).fetch("GET", BASE + "/x")
    with pytest.raises(NetworkError, match="boom"):
        session_with(WebDriverException("boom")).fetch("GET", BASE + "/x")
    with pytest.raises(StakeAPIError, match="not open"):
        BrowserSession(BASE, verbose=False).fetch("GET", BASE + "/x")


def test_is_logged_in_reads_the_users_id():
    assert session_with(LOGGED_IN).is_logged_in() is True
    assert session_with(LOGGED_OUT).is_logged_in() is False
    assert (
        session_with({"status": 200, "headers": {}, "text": "<html>"}).is_logged_in()
        is False
    )
    assert session_with(WebDriverException("x")).is_logged_in() is False


def test_login_check_sends_the_session_cookie_as_access_token():
    session = session_with(LOGGED_IN)
    assert session.is_logged_in() is True
    headers = session._driver.calls[0][2]
    assert headers["X-Access-Token"] == "tok"

    anonymous = session_with(LOGGED_OUT)
    anonymous._driver.cookie_list = []
    assert anonymous.is_logged_in() is False
    assert "X-Access-Token" not in anonymous._driver.calls[0][2]


def test_wait_for_login_polls_until_logged_in():
    session = session_with(LOGGED_OUT, LOGGED_OUT, LOGGED_IN)
    session.wait_for_login(timeout=5, poll=0)
    assert session._driver.replies == []


def test_wait_for_login_returns_at_once_when_already_logged_in():
    session = session_with(LOGGED_IN)
    session.wait_for_login(timeout=5, poll=0)


def test_wait_for_login_times_out():
    session = session_with(LOGGED_OUT, LOGGED_OUT)
    with pytest.raises(AuthenticationError, match="Not logged in"):
        session.wait_for_login(timeout=0, poll=0)


def test_wait_for_login_notices_a_closed_window():
    session = session_with(LOGGED_OUT)
    session._driver.alive = False
    with pytest.raises(NetworkError, match="closed"):
        session.wait_for_login(timeout=5, poll=0)
    assert not session.started


def test_cookies_use_the_json_export_shape():
    session = session_with()
    cookies = session.cookies()
    assert cookies[0] == {
        "domain": "stake1017.com", "name": "session", "value": "tok", "path": "/",
        "secure": True, "httpOnly": False, "expirationDate": 2000000000.0,
    }  # fmt: skip
    assert session.cookie_header() == "session=tok; locale=en"
    assert session.user_agent() == "Mozilla/5.0 Test"


def test_start_without_selenium_gives_install_hint(monkeypatch):
    monkeypatch.setitem(sys.modules, "selenium", None)
    with pytest.raises(StakeAPIError, match=r"stakeapi\[browser\]"):
        BrowserSession(BASE, verbose=False).start()


def test_only_the_login_cookie_is_copied_from_your_browser(monkeypatch):
    imported = ImportedCookies(
        cookies=[
            {
                "name": "session",
                "value": "tok",
                "path": "/",
                "secure": True,
                "expirationDate": 2000000000.5,
            },
            {"name": "KP_UIDz", "value": "bot", "path": "/"},
            {"name": "_ga", "value": "ga", "path": "/"},
        ],
        profile="Profile 2", browser="chrome", logged_in=True,
    )  # fmt: skip
    monkeypatch.setattr(chrome_cookies, "load_chrome_cookies", lambda *a, **k: imported)
    session = session_with()
    session.import_cookies_from = "chrome"
    session._import_login_cookie()
    assert session._driver.added == [
        {
            "name": "session",
            "value": "tok",
            "path": "/",
            "secure": True,
            "expiry": 2000000000,
        }
    ]
    assert session._driver.refreshed


def test_failed_cookie_import_falls_back_to_manual_login(monkeypatch):
    def fail(*args, **kwargs):
        raise StakeAPIError("no cookies")

    monkeypatch.setattr(chrome_cookies, "load_chrome_cookies", fail)
    session = session_with()
    session.import_cookies_from = "chrome"
    session._import_login_cookie()
    assert session._driver.added == [] and not session._driver.refreshed


def test_profile_dir_defaults_to_the_cache_folder(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert (
        default_profile_dir(BASE)
        == tmp_path / "stakeapi" / "chrome-profile-stake1017.com"
    )


def test_close_quits_the_driver():
    session = session_with()
    driver = session._driver
    session.close()
    assert driver.closed and not session.started
    session.close()


# --- the client's browser transport ----------------------------------------


class FakeBrowser:
    """Stands in for BrowserSession when testing the client."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.started = False
        self.closed = False
        self.waited = None
        self.requests = []

    def start(self):
        self.started = True

    def wait_for_login(self, timeout):
        self.waited = timeout

    def fetch(self, method, url, params, body, headers):
        self.requests.append((method, url, params, body, headers))
        return self.replies.pop(0)

    def cookies(self):
        return [
            {"name": "session", "value": "tok"},
            {"name": "cf_clearance", "value": "cf"},
        ]

    def cookie_header(self):
        return "session=tok; cf_clearance=cf"

    def user_agent(self):
        return "Mozilla/5.0 Test"

    def close(self):
        self.started = False
        self.closed = True


OK = (200, {"Content-Type": "application/json"}, '{"data": {"x": 1}}')


@pytest.mark.asyncio
async def test_client_logs_in_through_the_browser_and_adopts_its_credentials():
    browser = FakeBrowser(OK)
    async with StakeAPI(base_url=BASE, browser=browser) as client:
        assert browser.started and browser.waited == 300.0
        assert client.access_token == "tok" and client.session_cookie == "tok"
        assert client.cf_clearance == "cf" and client.user_agent == "Mozilla/5.0 Test"

        data = await client._graphql_request("query Q { x }", operation_name="Q")
        assert data == {"x": 1}
        method, url, _, body, headers = browser.requests[0]
        assert (method, url) == ("POST", BASE + "/_api/graphql")
        assert body["query"] == "query Q { x }"
        assert headers["X-Access-Token"] == "tok" and headers["X-Operation-Name"] == "Q"
    assert browser.closed


@pytest.mark.asyncio
async def test_login_timeout_zero_skips_the_wait():
    browser = FakeBrowser(OK)
    client = StakeAPI(base_url=BASE, browser=browser)
    client._browser_login_timeout = 0
    async with client:
        assert browser.started and browser.waited is None


@pytest.mark.asyncio
async def test_request_starts_the_browser_when_not_entered():
    browser = FakeBrowser(OK)
    client = StakeAPI(base_url=BASE, browser=browser)
    await client._request("GET", "/_api/x")
    assert browser.started
    await client.close()


@pytest.mark.asyncio
async def test_status_handling_is_the_same_through_the_browser():
    browser = FakeBrowser(
        (403, {"x-kpsdk-ct": "1"}, "no"),
        (401, {}, ""),
        (200, {}, "<html>"),
    )
    async with StakeAPI(base_url=BASE, browser=browser) as client:
        with pytest.raises(StakeAPIError, match="Kasada") as err:
            await client._request("GET", "/a")
        assert "automated Chrome window" in str(err.value)
        with pytest.raises(AuthenticationError):
            await client._request("GET", "/b")
        with pytest.raises(NetworkError, match="non-JSON"):
            await client._request("GET", "/c")


@pytest.mark.asyncio
async def test_reload_cookies_leaves_the_browser_open(tmp_path):
    path = tmp_path / "cookie.txt"
    path.write_text("session=aaa")
    browser = FakeBrowser()
    client = StakeAPI(base_url=BASE, browser=browser, cookie_file=str(path))
    browser.started = True
    await client.reload_cookies()
    assert not browser.closed
    await client.close()
    assert browser.closed


def test_with_browser_builds_a_session_without_opening_it():
    client = StakeAPI.with_browser(
        BASE, login_timeout=60, headless=True, profile_dir="/x"
    )
    assert client._browser_login_timeout == 60
    assert client._browser.headless and str(client._browser.profile_dir) == "/x"
    assert not client._browser.started


def test_from_chrome_uses_the_imported_login(monkeypatch):
    imported = ImportedCookies(
        cookies=[{"name": "session", "value": "tok"}, {"name": "a", "value": "b"}],
        profile="Default", browser="chrome", logged_in=True,
    )  # fmt: skip
    seen = {}

    def fake_load(domain, browser, profile):
        seen.update(domain=domain, browser=browser, profile=profile)
        return imported

    monkeypatch.setattr(chrome_cookies, "load_chrome_cookies", fake_load)
    client = StakeAPI.from_chrome(BASE, profile="Default")
    assert seen == {
        "domain": "stake1017.com",
        "browser": "chrome",
        "profile": "Default",
    }
    assert client.access_token == "tok" and client._cookie_header == "session=tok; a=b"


def test_from_chrome_failure_is_a_stake_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "browser_cookie3", None)
    with pytest.raises(StakeAPIError):
        StakeAPI.from_chrome(BASE)
    assert issubclass(ValidationError, StakeAPIError)
