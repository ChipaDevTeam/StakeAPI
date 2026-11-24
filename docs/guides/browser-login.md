---
layout: default
title: Browser Login
parent: Guides
nav_order: 11
---

# Browser Login & Chrome Cookies
{: .fs-9 }

Log in through a real Chrome window, or reuse the login you already have in Chrome.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Why

Plain HTTP calls from Python are often refused with `403 Forbidden` by the site's bot protection, even with valid cookies. Requests that come from a genuine browser tab are accepted. `StakeAPI.with_browser()` opens a real Chrome window (through chromedriver), waits while **you** log in, and then sends the library's requests with `fetch` from inside that page.

Nothing is typed for you, and the library adds no stealth or anti-detection tricks. The automated Chrome identifies itself as automated, and if the site refuses it, requests are refused too.

{: .highlight }
> **Recommended:** if you are logged in to the site in your normal Chrome, use `import_cookies_from="chrome"` ([below](#log-in-automatically-with-your-own-chrome)). The automated window is logged in at once, with no password, captcha or Google sign-in. Logging in by hand inside the automated window can fail: the site's captcha may not load there, and Google refuses sign-in in automated browsers ("This browser or app may not be secure").

## Install

```bash
pip install "stakeapi[browser]"
```

You need Chrome. The first time, Selenium downloads a chromedriver that matches your Chrome.

## Log in once

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI.with_browser("https://stake1017.com") as client:
        print(await client.get_account_status())
        print(await client.get_sports(limit=3))

asyncio.run(main())
```

1. Chrome opens at the site's sign-in dialog.
2. You log in (email, password, 2FA, captcha, whatever the site asks).
3. As soon as the site reports you as logged in, the `async with` block continues.

The login is kept in a Chrome profile folder (`~/.cache/stakeapi/chrome-profile-<host>`), so **the next run needs no login** until the session expires. Every method works the same as with a plain client, including the [WebSocket feeds](websockets.md), which reuse the browser's cookies.

| Option | Meaning |
|:-------|:--------|
| `login_timeout=300` | Seconds to wait for you to log in. `0` skips the wait, which is enough for public data. |
| `profile_dir=` | Where the Chrome profile (and your login) is kept |
| `chrome_binary=` | Path to Chrome, if it is not found |
| `chromedriver_path=` | Use your own chromedriver instead of letting Selenium fetch one |
| `import_cookies_from=` | `"chrome"`, `"chromium"`, `"brave"` or `"edge"`: log in automatically, see below |
| `chrome_profile=` | Profile of that browser, e.g. `"Profile 2"` |
| `headless=False` | See the note below |
| `verbose=True` | Print short progress messages to stderr |

{: .warning }
> **Headless Chrome was refused.** In testing, the site answered a headless Chrome with a Cloudflare block page (403), while a normal window worked. Keep `headless=False` unless you only need a connection that is already allowed.

## Log in automatically with your own Chrome

If you are already logged in to the site in your normal Chrome, the library can copy that login into the automated window, so there is nothing to type:

```python
async with StakeAPI.with_browser(
    "https://stake1017.com",
    import_cookies_from="chrome",
) as client:
    print(await client.get_user_balance())
```

Only the `session` cookie (the login) is copied, and only for the domain you pass. The site's bot-protection cookies are tied to the browser that earned them, so they stay behind. If you have several Chrome profiles, the one that is logged in to the site is used; pick another with `chrome_profile="Profile 2"`.

If the import fails (no login found, keyring locked), the window simply asks you to log in by hand.

## Save your Chrome cookies to a file

```bash
python -m stakeapi.chrome_cookies --domain stake1017.com --out cookies.json
```

(also available as `stakeapi-cookies` once installed). It reads the cookies of that one domain from your Chrome, writes them to a file only you can read, and prints only counts, never values:

```
Saved 28 cookies for stake1017.com from chrome profile 'Default' to cookies.json (logged in: yes).
```

Options: `--browser chrome|chromium|brave|edge`, `--profile "Profile 2"`, `--format json|header` (`header` writes a `cookie.txt` style line). The file works with `StakeAPI(cookie_file="cookies.json")`.

From Python:

```python
client = StakeAPI.from_chrome("https://stake1017.com")          # uses your Chrome's cookies
```

{: .note }
> A plain HTTP client built from Chrome's cookies still comes from a script, not a browser, so logged-in calls may get a 403 from the bot protection. Public data and the live feeds are the most likely to work. For logged-in calls, use `with_browser()`.

## Log in from the command line

```bash
python -m stakeapi.browser --base-url https://stake1017.com --out cookies.json
```

(also `stakeapi-login`). It opens Chrome, waits for you to log in, and optionally saves the cookies. Add `--import-from chrome` to copy your login instead.

## Good to know

- **A cookie file and the profile folder are live logins.** Keep them out of git and do not share them; log out of the session in your browser if one leaks. The profile folder is created with owner-only permissions.
- **One Chrome per profile folder.** Close the automated window before starting another client with the same `profile_dir`.
- **Reading Chrome's cookies** needs the key Chrome keeps in your system keyring (GNOME Keyring or KWallet on Linux), so the keyring has to be unlocked. Tested on Linux with Chrome 156. macOS and Windows paths are supported but untested, and recent Windows Chrome versions encrypt cookies in a way other programs cannot read; use the browser login there.
- **Betting still needs `allow_betting=True`** and every bet method still supports `dry_run=True`.
