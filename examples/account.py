"""
Account data example for StakeAPI: VIP progress, bonuses, seeds and stats.

Needs a logged-in session: put your browser's Cookie header in ./cookie.txt
(or set the STAKE_* variables in .env), the same as basic_usage.py.
get_user_stats() works without logging in.
"""

import asyncio

from basic_usage import make_client
from stakeapi.exceptions import PermissionDeniedError, StakeAPIError


async def main():
    async with make_client() as client:
        try:
            status = await client.get_account_status()
            print(f"Logged in as {status['name']} (KYC: {status['kycStatus']})")

            vip = await client.get_vip_info()
            print("VIP flags:", [f["flag"] for f in vip.get("flags") or []])
            print("VIP progress:", vip.get("flagProgress"))
            rakeback = (vip.get("rakeback") or {}).get("balances") or []
            print("Rakeback:", {b["currency"]: b["availableAmount"] for b in rakeback})

            print("Claimable bonuses:", await client.get_claimable_bonuses())

            seeds = await client.get_seed_pair()
            print(f"Server seed hash {seeds['server_seed_hash']}, nonce {seeds['nonce']}")

            print("Top games this month:")
            for stat in await client.get_game_statistics(period="month", sort="wagered", limit=5):
                print(f"  {stat['game']['name']}: {stat['betCount']} bets, profit {stat['profitValue']}")

            for bet in await client.get_sport_bet_history(limit=3):
                print(f"Sport bet {bet['amount']} {bet['currency']} @ {bet['potentialMultiplier']}x")
        except PermissionDeniedError as e:
            print(f"Not logged in: {e}")
        except StakeAPIError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
