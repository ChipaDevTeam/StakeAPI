"""Drives a real headless Chrome against a local fake site.

Skipped unless STAKEAPI_BROWSER_TESTS=1 (needs Chrome; Selenium downloads a
matching chromedriver the first time). Run with:

    STAKEAPI_BROWSER_TESTS=1 pytest tests/test_browser_live.py
"""

import asyncio
import os

import pytest
from aiohttp import web

from stakeapi import StakeAPI
from stakeapi.browser import BrowserSession

pytestmark = pytest.mark.skipif(
    not os.environ.get("STAKEAPI_BROWSER_TESTS"),
    reason="set STAKEAPI_BROWSER_TESTS=1 to run tests that open Chrome",
)


async def home(request):
    return web.Response(
        text="<html><body>fake site</body></html>", content_type="text/html"
    )


async def graphql(request):
    body = await request.json()
    logged_in = request.cookies.get("session") == "good"
    user = {"id": "u1"} if logged_in else None
    return web.json_response(
        {
            "data": {"user": user, "echo": body.get("query")},
            "seen": {
                "token": request.headers.get("X-Access-Token"),
                "operation": request.headers.get("X-Operation-Name"),
                "cookie": request.headers.get("Cookie"),
            },
        }
    )


async def blocked(request):
    return web.Response(status=403, text="no", headers={"x-kpsdk-ct": "1"})


@pytest.fixture
async def site():
    app = web.Application()
    app.router.add_get("/", home)
    app.router.add_post("/_api/graphql", graphql)
    app.router.add_get("/blocked", blocked)
    runner = web.AppRunner(app)
    await runner.setup()
    server = web.TCPSite(runner, "127.0.0.1", 0)
    await server.start()
    port = server._server.sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}"
    await runner.cleanup()


@pytest.mark.asyncio
async def test_real_chrome_sends_requests_from_the_page(site, tmp_path):
    session = BrowserSession(
        site, headless=True, profile_dir=str(tmp_path / "profile"), verbose=False
    )
    client = StakeAPI(base_url=site, browser=session, access_token="tok")
    client._browser_login_timeout = 0
    try:
        async with client:
            assert session.started
            assert await asyncio.to_thread(session.is_logged_in) is False

            data = await client._graphql_request("query Q { x }", operation_name="Q")
            assert data["echo"] == "query Q { x }"

            reply = await client._request(
                "POST",
                "/_api/graphql",
                data={"query": "q"},
                headers={"X-Operation-Name": "Op"},
            )
            assert reply["seen"]["token"] == "tok"
            assert reply["seen"]["operation"] == "Op"

            await asyncio.to_thread(
                session._driver.add_cookie, {"name": "session", "value": "good"}
            )
            assert await asyncio.to_thread(session.is_logged_in) is True
            await asyncio.to_thread(session.wait_for_login, 5, 0.1)

            await client._refresh_credentials()
            assert client.session_cookie == "good"
            assert "session=good" in (client._cookie_header or "")
            assert "Chrome" in (client.user_agent or "")

            with pytest.raises(Exception, match="Kasada"):
                await client._request("GET", "/blocked")
    finally:
        await client.close()
    assert not session.started
