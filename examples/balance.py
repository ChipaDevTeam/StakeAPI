import asyncio
import os

import dotenv

from stakeapi import (
    AuthenticationError,
    NetworkError,
    PermissionDeniedError,
    RateLimitError,
    StakeAPI,
    StakeAPIError,
)

dotenv.load_dotenv()


async def main():
    # Replace with your actual access token
    access_token = os.getenv("STAKE_ACCESS_TOKEN")
    session_cookie = os.getenv("STAKE_SESSION_COOKIE")
    cf_clearance = os.getenv("STAKE_CF_CLEARANCE")
    user_agent = os.getenv("STAKE_USER_AGENT")
    # Use a regional mirror if stake.com is blocked in your country,
    # e.g. STAKE_BASE_URL=https://stake1017.com
    base_url = os.getenv("STAKE_BASE_URL", "https://stake.com")

    # Alternative auth: put the entire Cookie header from your browser in a
    # file (DevTools → Network → any request → 'cookie' header) and point
    # STAKE_COOKIE_FILE at it. Falls back to ./cookie.txt if it exists.
    cookie_file = os.getenv("STAKE_COOKIE_FILE")
    if not cookie_file and os.path.exists("cookie.txt"):
        cookie_file = "cookie.txt"

    async with StakeAPI(
        access_token=access_token,
        session_cookie=session_cookie,
        cf_clearance=cf_clearance,
        user_agent=user_agent,
        base_url=base_url,
        cookie_file=cookie_file,
    ) as client:

        # 1. Get your balance
        balance = await client.get_user_balance()
        print("💰 Your Balance:")
        if balance["available"]:
            for currency, amount in balance["available"].items():
                if amount > 0:
                    print(f"  {currency.upper()}: {amount}")
            if not any(amount > 0 for amount in balance["available"].values()):
                print("  (all balances are 0)")
        else:
            print("  (no balance data returned)")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except PermissionDeniedError as e:
        print(f"❌ Permission denied: {e}")
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
    except RateLimitError as e:
        print(f"❌ Rate limited: {e}")
    except NetworkError as e:
        print(f"❌ Network problem: {e}")
    except StakeAPIError as e:
        print(f"❌ API error: {e}")
