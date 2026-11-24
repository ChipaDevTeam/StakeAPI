"""Tests for how the client holds and refreshes credentials."""

import pytest
from aiohttp import web

from stakeapi import StakeAPI
from stakeapi.exceptions import AuthenticationError, StakeAPIError, ValidationError


async def echo(request):
    return web.json_response(
        {
            "token": request.headers.get("X-Access-Token"),
            "cookie": request.headers.get("Cookie"),
        }
    )


async def cloudflare_block(request):
    return web.Response(
        status=403,
        text='<div id="cf-error-details">Sorry</div>',
        content_type="text/html",
    )


async def kasada_block(request):
    return web.Response(status=403, headers={"x-kpsdk-ct": "abc"}, text="blocked")


async def plain_block(request):
    return web.Response(status=403, text="")


async def unauthorized(request):
    return web.Response(status=401, text="")


@pytest.fixture
async def base_url():
    app = web.Application()
    app.router.add_get("/echo", echo)
    app.router.add_get("/cf", cloudflare_block)
    app.router.add_get("/kasada", kasada_block)
    app.router.add_get("/plain", plain_block)
    app.router.add_get("/401", unauthorized)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}"
    await runner.cleanup()


def test_credentials_live_in_the_auth_manager():
    client = StakeAPI(access_token="a", session_cookie="s")
    assert (client.access_token, client.session_cookie) == ("a", "s")
    client.access_token = "b"
    assert client._auth_manager.access_token == "b"


@pytest.mark.asyncio
async def test_new_token_applies_to_the_next_request(base_url):
    async with StakeAPI(access_token="old", base_url=base_url) as client:
        assert (await client._request("GET", "/echo"))["token"] == "old"
        client.set_access_token("new")
        assert (await client._request("GET", "/echo"))["token"] == "new"
        client.access_token = "newer"
        assert (await client._request("GET", "/echo"))["token"] == "newer"


@pytest.mark.asyncio
async def test_reload_cookies_picks_up_a_changed_file(base_url, tmp_path):
    path = tmp_path / "cookie.txt"
    path.write_text("session=aaa; locale=en")
    async with StakeAPI(base_url=base_url, cookie_file=str(path)) as client:
        first = await client._request("GET", "/echo")
        assert first["token"] == "aaa" and "session=aaa" in first["cookie"]

        path.write_text("session=bbb; locale=en")
        await client.reload_cookies()

        second = await client._request("GET", "/echo")
        assert second["token"] == "bbb" and "session=bbb" in second["cookie"]
        assert client.session_cookie == "bbb"


@pytest.mark.asyncio
async def test_reload_keeps_an_explicit_token(base_url, tmp_path):
    path = tmp_path / "cookie.txt"
    path.write_text("session=aaa")
    client = StakeAPI(access_token="mine", base_url=base_url, cookie_file=str(path))
    path.write_text("session=bbb")
    await client.reload_cookies()
    assert client.access_token == "mine"
    assert client.session_cookie == "bbb"
    await client.close()


@pytest.mark.asyncio
async def test_reload_needs_a_cookie_file():
    client = StakeAPI(access_token="x")
    with pytest.raises(ValidationError, match="cookie_file"):
        await client.reload_cookies()


@pytest.mark.asyncio
async def test_reload_reports_a_broken_file(base_url, tmp_path):
    path = tmp_path / "cookie.txt"
    path.write_text("session=aaa")
    client = StakeAPI(base_url=base_url, cookie_file=str(path))
    path.write_text("")
    with pytest.raises(ValidationError):
        await client.reload_cookies()
    assert client.access_token == "aaa"


@pytest.mark.asyncio
async def test_client_works_again_after_close(base_url):
    client = StakeAPI(access_token="t", base_url=base_url)
    assert (await client._request("GET", "/echo"))["token"] == "t"
    await client.close()
    assert (await client._request("GET", "/echo"))["token"] == "t"
    await client.close()


@pytest.mark.asyncio
async def test_403_from_cloudflare_block_page(base_url):
    async with StakeAPI(access_token="t", base_url=base_url) as client:
        with pytest.raises(StakeAPIError, match="Cloudflare block page") as err:
            await client._request("GET", "/cf")
    assert "No cookies were sent" in str(err.value)
    assert "user_agent=" in str(err.value)


@pytest.mark.asyncio
async def test_403_from_kasada(base_url):
    async with StakeAPI(
        base_url=base_url, cookie_string="session=abc; cf_clearance=x"
    ) as client:
        with pytest.raises(StakeAPIError, match="Kasada") as err:
            await client._request("GET", "/kasada")
    assert "No cookies were sent" not in str(err.value)
    assert "no cf_clearance" not in str(err.value).lower()


@pytest.mark.asyncio
async def test_403_without_cf_clearance_says_so(base_url):
    async with StakeAPI(base_url=base_url, cookie_string="session=abc") as client:
        with pytest.raises(StakeAPIError, match="bot protection") as err:
            await client._request("GET", "/plain")
    assert "no cf_clearance" in str(err.value)
    assert "does not work around" in str(err.value)


@pytest.mark.asyncio
async def test_401_tells_how_to_refresh(base_url):
    async with StakeAPI(access_token="t", base_url=base_url) as client:
        with pytest.raises(AuthenticationError, match="reload_cookies"):
            await client._request("GET", "/401")
