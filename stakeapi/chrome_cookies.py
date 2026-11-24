"""Import the cookies of a site from your own Chrome (or Chromium, Brave, Edge).

Only cookies for the one domain you ask for are read; values are never
printed. The cookie store is decrypted with the key Chrome keeps in your
system keyring, the same way the browser does, so this works while you are
logged in to the site in that browser.

Needs ``pip install "stakeapi[browser]"`` (it uses ``browser-cookie3``).

Command line:

    python -m stakeapi.chrome_cookies --domain stake1017.com --out cookies.json
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .exceptions import StakeAPIError

SUPPORTED_BROWSERS = ("chrome", "chromium", "brave", "edge")

# Chrome keeps the login in this cookie
LOGIN_COOKIE = "session"


@dataclass
class ImportedCookies:
    """Cookies read from a browser profile."""

    cookies: List[Dict[str, Any]]
    profile: str
    browser: str
    logged_in: bool  # the profile has a login (session) cookie for the domain

    def header(self) -> str:
        """The cookies as a Cookie header string (name=value; ...)."""
        return "; ".join(f"{c['name']}={c['value']}" for c in self.cookies)


def user_data_dirs(browser: str = "chrome") -> List[Path]:
    """Where the browser keeps its profiles on this operating system."""
    home = Path.home()
    if sys.platform.startswith("linux"):
        table = {
            "chrome": [".config/google-chrome", ".config/google-chrome-beta"],
            "chromium": [".config/chromium", "snap/chromium/common/chromium"],
            "brave": [".config/BraveSoftware/Brave-Browser"],
            "edge": [".config/microsoft-edge"],
        }
        roots = [home / r for r in table.get(browser, [])]
    elif sys.platform == "darwin":
        base = home / "Library" / "Application Support"
        table = {
            "chrome": ["Google/Chrome"],
            "chromium": ["Chromium"],
            "brave": ["BraveSoftware/Brave-Browser"],
            "edge": ["Microsoft Edge"],
        }
        roots = [base / r for r in table.get(browser, [])]
    else:
        local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        table = {
            "chrome": ["Google/Chrome/User Data"],
            "chromium": ["Chromium/User Data"],
            "brave": ["BraveSoftware/Brave-Browser/User Data"],
            "edge": ["Microsoft/Edge/User Data"],
        }
        roots = [local / r for r in table.get(browser, [])]
    return [r for r in roots if r.is_dir()]


def _cookie_db(profile_dir: Path) -> Optional[Path]:
    for candidate in (profile_dir / "Network" / "Cookies", profile_dir / "Cookies"):
        if candidate.is_file():
            return candidate
    return None


def find_profiles(
    browser: str = "chrome", user_data_dir: Optional[Path] = None
) -> List[Tuple[str, Path]]:
    """List (profile name, cookie database) for every profile that has cookies."""
    roots = [user_data_dir] if user_data_dir else user_data_dirs(browser)
    found = []
    for root in roots:
        for entry in sorted(root.iterdir()):
            if entry.is_dir() and (
                entry.name == "Default" or entry.name.startswith("Profile ")
            ):
                db = _cookie_db(entry)
                if db:
                    found.append((entry.name, db))
    return found


def _to_dict(cookie: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "domain": cookie.domain,
        "name": cookie.name,
        "value": cookie.value,
        "path": cookie.path or "/",
        "secure": bool(cookie.secure),
    }
    if cookie.expires:
        out["expirationDate"] = float(cookie.expires)
    return out


def load_chrome_cookies(
    domain: str,
    browser: str = "chrome",
    profile: Optional[str] = None,
    user_data_dir: Optional[Path] = None,
) -> ImportedCookies:
    """
    Read the cookies of ``domain`` from a browser profile on this computer.

    Args:
        domain: Host to read cookies for, e.g. "stake1017.com". Cookies for its
            parent and subdomains that apply to the host are included.
        browser: "chrome", "chromium", "brave" or "edge"
        profile: Profile folder name, e.g. "Default" or "Profile 2". When omitted
            every profile is checked and the one logged in to the site is used.
        user_data_dir: Browser data folder, for non-standard installs.

    Raises:
        StakeAPIError: browser-cookie3 is not installed, the browser or profile
            is not found, the cookies cannot be decrypted, or the site has no
            cookies there.
    """
    if browser not in SUPPORTED_BROWSERS:
        raise StakeAPIError(
            f"Unsupported browser {browser!r}; "
            f"use one of {', '.join(SUPPORTED_BROWSERS)}"
        )
    try:
        import browser_cookie3
    except ImportError:
        raise StakeAPIError(
            "Importing browser cookies needs browser-cookie3: "
            'pip install "stakeapi[browser]"'
        )

    profiles = find_profiles(browser, user_data_dir)
    if profile:
        profiles = [p for p in profiles if p[0] == profile]
    if not profiles:
        where = profile or "any profile"
        raise StakeAPIError(
            f"No {browser} cookie database found for {where}. "
            "Is the browser installed, and is the profile name right "
            "(for example 'Default' or 'Profile 2')?"
        )

    reader = getattr(browser_cookie3, browser)
    now = time.time()
    best: Optional[ImportedCookies] = None
    errors = []
    for name, db in profiles:
        try:
            jar = reader(cookie_file=str(db), domain_name=domain)
        except Exception as e:  # browser_cookie3 raises several kinds
            errors.append(f"{name}: {e}")
            continue
        unique: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        for cookie in jar:
            if cookie.expires and cookie.expires < now:
                continue
            unique[(cookie.domain, cookie.path, cookie.name)] = _to_dict(cookie)
        cookies = list(unique.values())
        if not cookies:
            continue
        candidate = ImportedCookies(
            cookies=cookies,
            profile=name,
            browser=browser,
            logged_in=any(c["name"] == LOGIN_COOKIE for c in cookies),
        )
        if best is None or (candidate.logged_in, len(cookies)) > (
            best.logged_in,
            len(best.cookies),
        ):
            best = candidate

    if best is None:
        if errors:
            raise StakeAPIError(
                f"Could not read {browser} cookies ({'; '.join(errors)}). "
                "Chrome's cookie key lives in your system keyring (GNOME Keyring or "
                "KWallet): unlock it, and run this as the user who owns the profile."
            )
        raise StakeAPIError(
            f"No cookies for {domain} in {browser}. Open the site in that browser "
            "and log in first."
        )
    return best


def save_cookies(path: str, imported: ImportedCookies, fmt: str = "json") -> None:
    """Write the cookies to a file only you can read (mode 0600)."""
    if fmt == "json":
        text = json.dumps(imported.cookies, indent=2)
    elif fmt == "header":
        text = imported.header() + "\n"
    else:
        raise StakeAPIError(f"Unknown format {fmt!r}; use 'json' or 'header'")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(path, 0o600)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m stakeapi.chrome_cookies",
        description="Save the cookies of one site from your own Chrome to a file.",
    )
    parser.add_argument(
        "--domain", default="stake.com", help="site host, e.g. stake1017.com"
    )
    parser.add_argument("--browser", default="chrome", choices=SUPPORTED_BROWSERS)
    parser.add_argument(
        "--profile",
        help='profile folder, e.g. "Profile 2" (default: the logged-in one)',
    )
    parser.add_argument(
        "--out", default="cookies.json", help="output file (default: cookies.json)"
    )
    parser.add_argument("--format", default="json", choices=("json", "header"))
    args = parser.parse_args(argv)

    try:
        imported = load_chrome_cookies(args.domain, args.browser, args.profile)
        save_cookies(args.out, imported, args.format)
    except StakeAPIError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(
        f"Saved {len(imported.cookies)} cookies for {args.domain} from "
        f"{args.browser} profile {imported.profile!r} to {args.out} "
        f"(logged in: {'yes' if imported.logged_in else 'no'})."
    )
    print("This file is a live login. Keep it out of git and do not share it.")
    if not imported.logged_in:
        print(
            f"No '{LOGIN_COOKIE}' cookie found: "
            "log in to the site in that browser first."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
