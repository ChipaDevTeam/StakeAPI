"""
Public data examples for StakeAPI: casino lobby, sports odds, promotions.

None of these calls need a logged-in account, but requests still have to
pass Cloudflare, so set up cookies the same way as basic_usage.py
(./cookie.txt or the STAKE_* variables in .env).
"""

import asyncio

from basic_usage import make_client
from stakeapi.exceptions import StakeAPIError


async def casino_examples(client):
    print("=== Casino ===")
    for game in (await client.get_casino_games("stake-originals", limit=5)):
        print(f"  {game.name:<12} RTP {game.rtp}%  players: {game.player_count}")

    dice = await client.get_game_details("stake-dice")
    print(f"  Dice is by {dice.provider}, tags: {', '.join(dice.features)}")

    providers = await client.get_casino_collection("provider")
    print(f"  {len(providers)} providers, top: {providers[0]['translation']}")

    crash = await client.get_crash_history(limit=5)
    print("  Last crash points:", [round(r["crashpoint"], 2) for r in crash])

    plinko = (await client.get_game_payouts())["plinko"][0]
    print(f"  Plinko {plinko['rows']} rows / {plinko['risk']}: {plinko['payouts']}")


async def sports_examples(client):
    print("\n=== Sports ===")
    sports = await client.get_sports(limit=5)
    print("  Sports:", ", ".join(f"{s['name']} ({s['fixtureCount']})" for s in sports))

    for event in (await client.get_sports_events("soccer"))[:3]:
        print(f"  {event.home_team} vs {event.away_team}: {event.odds}")

    epl = await client.get_tournament("soccer", "england", "premier-league", limit=3)
    print(f"  {epl['name']}: {epl['fixtureCount']} upcoming fixtures")

    for match in (await client.get_trending_matches())[:3]:
        users = match["fixtureStatistics"]["totalUserCount"]
        print(f"  Trending: {match['fixture']['name']} ({users} bettors)")


async def promotion_examples(client):
    print("\n=== Promotions ===")
    for race in await client.get_active_races(leaderboard_limit=3):
        print(f"  {race['name']} ends {race['endTime']}")

    challenges = await client.get_challenges(limit=3)
    print(f"  {challenges['count']} open challenges")


async def main():
    async with make_client() as client:
        try:
            await casino_examples(client)
            await sports_examples(client)
            await promotion_examples(client)
        except StakeAPIError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
