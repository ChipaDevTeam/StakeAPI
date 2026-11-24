"""Tests for importing cookies from Chrome (browser-cookie3 is faked)."""

import json
import stat
import sys
import time
import types
from http.cookiejar import Cookie

import pytest

from stakeapi import chrome_cookies
from stakeapi.chrome_cookies import load_chrome_cookies, main
from stakeapi.exceptions import StakeAPIError

FUTURE = int(time.time()) + 86400
PAST = int(time.time()) - 86400


def make_cookie(name, value, domain="stake1017.com", expires=FUTURE):
    return Cookie(
        0, name, value, None, False, domain, True, domain.startswith("."), "/",
        True, True, expires, expires is None, None, None, {},
    )  # fmt: skip


@pytest.fixture
def data_dir(tmp_path):
    """A Chrome data folder with three profiles that have cookie databases."""
    for name, sub in (("Default", ""), ("Profile 2", "Network"), ("Profile 3", "")):
        folder = tmp_path / name / sub
        folder.mkdir(parents=True)
        (folder / "Cookies").write_text("")
    (tmp_path / "System Profile").mkdir()
    (tmp_path / "System Profile" / "Cookies").write_text("")
    return tmp_path


@pytest.fixture
def fake_cookies(monkeypatch, data_dir):
    """Cookies each profile's database holds, plus the calls made to the reader."""

    class Profiles(dict):
        calls: list = []

    by_profile = Profiles()
    calls = by_profile.calls = []

    def chrome(cookie_file, domain_name):
        calls.append((cookie_file, domain_name))
        profile = cookie_file.split("/")[-3 if "Network" in cookie_file else -2]
        result = by_profile[profile]
        if isinstance(result, Exception):
            raise result
        return result

    module = types.ModuleType("browser_cookie3")
    module.chrome = chrome
    monkeypatch.setitem(sys.modules, "browser_cookie3", module)
    return by_profile


def test_picks_the_profile_that_is_logged_in(fake_cookies, data_dir):
    fake_cookies["Default"] = [
        make_cookie("a", "1"),
        make_cookie("b", "2"),
        make_cookie("c", "3"),
    ]
    fake_cookies["Profile 2"] = [
        make_cookie("session", "tok"),
        make_cookie("locale", "en"),
    ]
    fake_cookies["Profile 3"] = []
    imported = load_chrome_cookies("stake1017.com", user_data_dir=data_dir)
    assert imported.profile == "Profile 2"
    assert imported.logged_in
    assert imported.header() == "session=tok; locale=en"
    assert {c[1] for c in fake_cookies.calls} == {"stake1017.com"}


def test_explicit_profile(fake_cookies, data_dir):
    fake_cookies["Default"] = [make_cookie("a", "1")]
    fake_cookies["Profile 2"] = [make_cookie("session", "tok")]
    imported = load_chrome_cookies(
        "stake1017.com", profile="Default", user_data_dir=data_dir
    )
    assert imported.profile == "Default" and not imported.logged_in
    with pytest.raises(StakeAPIError, match="Profile 9"):
        load_chrome_cookies(
            "stake1017.com", profile="Profile 9", user_data_dir=data_dir
        )


def test_expired_cookies_are_skipped_and_converted(fake_cookies, data_dir):
    fake_cookies["Default"] = [
        make_cookie("session", "tok"),
        make_cookie("old", "x", expires=PAST),
        make_cookie("temp", "y", domain=".stake1017.com", expires=None),
    ]
    fake_cookies["Profile 2"] = fake_cookies["Profile 3"] = []
    imported = load_chrome_cookies("stake1017.com", user_data_dir=data_dir)
    names = [c["name"] for c in imported.cookies]
    assert names == ["session", "temp"]
    session = imported.cookies[0]
    assert session["domain"] == "stake1017.com" and session["expirationDate"] == FUTURE
    assert "expirationDate" not in imported.cookies[1]


def test_no_cookies_says_to_log_in_first(fake_cookies, data_dir):
    fake_cookies["Default"] = fake_cookies["Profile 2"] = fake_cookies["Profile 3"] = []
    with pytest.raises(StakeAPIError, match="log in first"):
        load_chrome_cookies("stake1017.com", user_data_dir=data_dir)


def test_decryption_failure_points_at_the_keyring(fake_cookies, data_dir):
    for name in ("Default", "Profile 2", "Profile 3"):
        fake_cookies[name] = RuntimeError("cannot decrypt")
    with pytest.raises(StakeAPIError, match="keyring"):
        load_chrome_cookies("stake1017.com", user_data_dir=data_dir)


def test_one_unreadable_profile_does_not_stop_the_others(fake_cookies, data_dir):
    fake_cookies["Default"] = RuntimeError("locked")
    fake_cookies["Profile 2"] = [make_cookie("session", "tok")]
    fake_cookies["Profile 3"] = []
    assert (
        load_chrome_cookies("stake1017.com", user_data_dir=data_dir).profile
        == "Profile 2"
    )


def test_missing_library_gives_install_hint(monkeypatch, data_dir):
    monkeypatch.setitem(sys.modules, "browser_cookie3", None)
    with pytest.raises(StakeAPIError, match=r"stakeapi\[browser\]"):
        load_chrome_cookies("stake1017.com", user_data_dir=data_dir)


def test_unsupported_browser():
    with pytest.raises(StakeAPIError, match="Unsupported"):
        load_chrome_cookies("stake1017.com", browser="netscape")


def test_cli_writes_a_private_file_and_prints_no_values(
    fake_cookies, data_dir, monkeypatch, tmp_path, capsys
):
    fake_cookies["Default"] = [make_cookie("session", "SECRET-TOKEN")]
    fake_cookies["Profile 2"] = fake_cookies["Profile 3"] = []
    monkeypatch.setattr(chrome_cookies, "user_data_dirs", lambda browser: [data_dir])
    out = tmp_path / "cookies.json"

    assert main(["--domain", "stake1017.com", "--out", str(out)]) == 0

    assert json.loads(out.read_text())[0]["value"] == "SECRET-TOKEN"
    assert stat.S_IMODE(out.stat().st_mode) == 0o600
    shown = capsys.readouterr().out
    assert "SECRET-TOKEN" not in shown
    assert "1 cookies" in shown and "logged in: yes" in shown


def test_cli_header_format_and_failure_exit_code(
    fake_cookies, data_dir, monkeypatch, tmp_path, capsys
):
    fake_cookies["Default"] = [make_cookie("session", "tok"), make_cookie("a", "b")]
    fake_cookies["Profile 2"] = fake_cookies["Profile 3"] = []
    monkeypatch.setattr(chrome_cookies, "user_data_dirs", lambda browser: [data_dir])
    out = tmp_path / "cookie.txt"
    assert (
        main(["--domain", "stake1017.com", "--out", str(out), "--format", "header"])
        == 0
    )
    assert out.read_text() == "session=tok; a=b\n"

    fake_cookies["Default"] = []
    assert main(["--domain", "stake1017.com", "--out", str(tmp_path / "x")]) == 1
    assert "Error:" in capsys.readouterr().err
