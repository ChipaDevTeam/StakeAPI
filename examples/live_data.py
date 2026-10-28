"""
Live data example for StakeAPI: watch Crash rounds and high-roller bets
over the site's WebSocket.

No login is needed, but the connection has to pass Cloudflare, so set up
cookies the same way as basic_usage.py (./cookie.txt or the STAKE_* variables
in .env). Stop with Ctrl+C.
"""

import asyncio

from basic_usage import make_client
from stakeapi.exceptions import StakeAPIError


async def watch_crash(ws):
    async for event in ws.crash():
        if event["__typename"] == "MultiplayerCrash" and event["status"] == "crash":
            print(f"[crash]     round ended at {event['multiplier']:.2f}x")


async def watch_highrollers(ws):
    async for entry in ws.highroller_bets():
        bet = entry.get("bet") or {}
        user = (bet.get("user") or {}).get("name") or "hidden"
        print(
            f"[highroller] {user} bet {bet.get('amount')} {bet.get('currency')} "
            f"on {entry['game']['name']} → {bet.get('payoutMultiplier')}x"
        )


async def main():
    async with make_client() as client:
        try:
            async with client.websocket() as ws:
                await asyncio.gather(watch_crash(ws), watch_highrollers(ws))
        except StakeAPIError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
