"""
Basic usage examples for StakeAPI.

This script demonstrates how to use the StakeAPI client for common operations.

Authentication (same as balance.py):
  - Easiest: put the entire Cookie header from your browser in ./cookie.txt
    (DevTools → Network tab → any request → copy the 'cookie' header),
    or point STAKE_COOKIE_FILE at the file.
  - Or set STAKE_ACCESS_TOKEN / STAKE_SESSION_COOKIE / STAKE_CF_CLEARANCE in .env.
  - If stake.com is blocked in your country, set STAKE_BASE_URL to a mirror,
    e.g. STAKE_BASE_URL=https://stake1017.com
  - STAKE_USER_AGENT must be the exact User-Agent of the browser your
    cookies came from.
"""

import asyncio
import os
from decimal import Decimal

import dotenv

from stakeapi import StakeAPI
from stakeapi.exceptions import (
    StakeAPIError,
    AuthenticationError,
    PermissionDeniedError,
    NetworkError,
)

dotenv.load_dotenv()


def make_client() -> StakeAPI:
    """Build a StakeAPI client from environment variables / cookie.txt."""
    cookie_file = os.getenv("STAKE_COOKIE_FILE")
    if not cookie_file and os.path.exists("cookie.txt"):
        cookie_file = "cookie.txt"

    return StakeAPI(
        access_token=os.getenv("STAKE_ACCESS_TOKEN"),
        session_cookie=os.getenv("STAKE_SESSION_COOKIE"),
        cf_clearance=os.getenv("STAKE_CF_CLEARANCE"),
        user_agent=os.getenv("STAKE_USER_AGENT"),
        base_url=os.getenv("STAKE_BASE_URL", "https://stake.com"),
        cookie_file=cookie_file,
    )


def has_credentials() -> bool:
    """Check that some form of authentication is configured."""
    return bool(
        os.getenv("STAKE_ACCESS_TOKEN")
        or os.getenv("STAKE_COOKIE_FILE")
        or os.path.exists("cookie.txt")
    )


async def basic_usage_example():
    """Demonstrate basic StakeAPI usage."""

    if not has_credentials():
        print("No credentials found — create cookie.txt or set STAKE_ACCESS_TOKEN in .env")
        return

    # Create client using context manager (recommended)
    async with make_client() as client:
        try:
            # Get account balance (GraphQL — works on all mirrors)
            print("Getting account balance...")
            balance = await client.get_user_balance()
            for currency, amount in balance["available"].items():
                if amount > 0:
                    print(f"  {currency.upper()}: {amount} (vault: {balance['vault'].get(currency, 0)})")
            if not any(amount > 0 for amount in balance["available"].values()):
                print("  (all balances are 0)")

            # Get user profile
            print("\nGetting user profile...")
            user = await client.get_user_profile()
            print(f"Welcome, {user.username}!")
            print(f"Account verified: {user.verified}")
            print(f"Default currency: {user.currency}")

        except PermissionDeniedError as e:
            print(f"Permission denied: {e}")
        except AuthenticationError:
            print("Authentication failed. Refresh your cookie.txt / access token.")
        except NetworkError as e:
            print(f"Network problem: {e}")
        except StakeAPIError as e:
            print(f"API error occurred: {e}")


async def game_search_example():
    """Demonstrate searching for specific games."""

    if not has_credentials():
        print("No credentials found — create cookie.txt or set STAKE_ACCESS_TOKEN in .env")
        return

    async with make_client() as client:
        try:
            # Get all casino games
            all_games = await client.get_casino_games()

            # Filter by provider
            pragmatic_games = [g for g in all_games if "pragmatic" in g.provider.lower()]
            print(f"Pragmatic Play games: {len(pragmatic_games)}")

            # Filter by RTP
            high_rtp_games = [g for g in all_games if g.rtp and g.rtp > 96.0]
            print(f"High RTP games (>96%): {len(high_rtp_games)}")

            # Filter by bet limits
            low_stakes = [g for g in all_games if g.min_bet <= Decimal("0.10")]
            print(f"Low minimum bet games (≤$0.10): {len(low_stakes)}")

        except StakeAPIError as e:
            print(f"Error searching games: {e}")


async def betting_example():
    """Demonstrate betting operations (use with caution!)."""

    if not has_credentials():
        print("No credentials found — create cookie.txt or set STAKE_ACCESS_TOKEN in .env")
        return

    async with make_client() as client:
        try:
            # Check balance first
            balance = await client.get_user_balance()
            usd_balance = balance["available"].get("usd", 0)

            if usd_balance < 10:
                print("Insufficient balance for demo betting")
                return

            # Example bet data (modify according to actual API requirements)
            bet_data = {
                "game_id": "example_game_id",
                "bet_type": "win",
                "amount": "1.00",
                "currency": "USD"
            }

            # Place bet (commented out for safety)
            # bet = await client.place_bet(bet_data)
            # print(f"Bet placed: {bet.id}")
            # print(f"Amount: ${bet.amount}")
            # print(f"Potential payout: ${bet.potential_payout}")

            print("Demo betting disabled for safety")
            print("Uncomment the bet placement code to enable")

        except StakeAPIError as e:
            print(f"Error placing bet: {e}")


async def main():
    """Run all examples."""
    print("=== StakeAPI Examples ===\n")

    print("1. Basic Usage Example")
    await basic_usage_example()

    print("\n" + "="*50 + "\n")

    print("2. Game Search Example")
    await game_search_example()

    print("\n" + "="*50 + "\n")

    print("3. Betting Example")
    await betting_example()


if __name__ == "__main__":
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)

    # Run examples
    asyncio.run(main())
