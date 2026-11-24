"""Tests for loading cookie files."""

import json
import time

import pytest

from stakeapi import StakeAPI
from stakeapi.auth import AuthManager
from stakeapi.exceptions import ValidationError

FUTURE = time.time() + 86400
PAST = time.time() - 86400


def write(tmp_path, content, name="cookies.json"):
    path = tmp_path / name
    path.write_text(content if isinstance(content, str) else json.dumps(content))
    return str(path)


def test_raw_cookie_header_still_works(tmp_path):
    path = write(tmp_path, "Cookie: session=abc;\n cf_clearance=xyz", "cookie.txt")
    assert AuthManager.load_cookie_file(path) == "session=abc; cf_clearance=xyz"


def test_browser_export_becomes_cookie_header(tmp_path):
    path = write(
        tmp_path,
        [
            {"domain": "stake1017.com", "name": "session", "value": "abc"},
            {"domain": ".stake1017.com", "name": "_ga", "value": "GA1.1"},
            {"domain": "stake1017.com", "name": "locale", "value": ""},
        ],
    )
    header = AuthManager.load_cookie_file(path, domain="stake1017.com")
    assert header == "session=abc; _ga=GA1.1; locale="


def test_expired_and_other_domain_cookies_are_dropped(tmp_path):
    path = write(
        tmp_path,
        [
            {
                "domain": "stake1017.com",
                "name": "keep",
                "value": "1",
                "expirationDate": FUTURE,
            },
            {
                "domain": "stake1017.com",
                "name": "old",
                "value": "2",
                "expirationDate": PAST,
            },
            {"domain": "example.com", "name": "other", "value": "3"},
            {"domain": "stake1017.com", "name": "nameless"},
        ],
    )
    assert AuthManager.load_cookie_file(path, domain="stake1017.com") == "keep=1"


def test_parent_domain_cookie_applies_to_subdomain(tmp_path):
    path = write(tmp_path, [{"domain": ".stake.com", "name": "a", "value": "1"}])
    assert AuthManager.load_cookie_file(path, domain="www.stake.com") == "a=1"


def test_name_value_object(tmp_path):
    path = write(tmp_path, {"session": "abc", "locale": "en"})
    assert AuthManager.load_cookie_file(path) == "session=abc; locale=en"


def test_wrong_domain_explains_mismatch(tmp_path):
    path = write(tmp_path, [{"domain": "stake1017.com", "name": "s", "value": "1"}])
    with pytest.raises(ValueError, match="stake1017.com"):
        AuthManager.load_cookie_file(path, domain="stake.com")


def test_malformed_json(tmp_path):
    path = write(tmp_path, "[{not json")
    with pytest.raises(ValueError, match="not valid JSON"):
        AuthManager.load_cookie_file(path)


def test_client_reads_session_from_json_export(tmp_path):
    path = write(
        tmp_path,
        [
            {"domain": "stake1017.com", "name": "session", "value": "tok123"},
            {"domain": "stake1017.com", "name": "cf_clearance", "value": "cf"},
        ],
    )
    client = StakeAPI(base_url="https://stake1017.com", cookie_file=path)
    assert client.access_token == "tok123"
    assert client.session_cookie == "tok123"
    assert client.cf_clearance == "cf"


def test_client_rejects_cookies_for_another_mirror(tmp_path):
    path = write(tmp_path, [{"domain": "stake1017.com", "name": "s", "value": "1"}])
    with pytest.raises(ValidationError, match="base_url"):
        StakeAPI(base_url="https://stake.com", cookie_file=path)
