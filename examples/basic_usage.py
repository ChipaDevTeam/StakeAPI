"""
Basic usage examples for StakeAPI.

This script demonstrates how to use the StakeAPI client for common operations.
"""

import asyncio
import os
from decimal import Decimal
from stakeapi import StakeAPI
from stakeapi.exceptions import StakeAPIError, AuthenticationError


async def basic_usage_example():
    """Demonstrate basic StakeAPI usage."""
    
    # Get API key from environment variable
    api_key = os.getenv("STAKE_API_KEY")
    if not api_key:
        print("Please set STAKE_API_KEY environment variable")
        return
    
    # Create client using context manager (recommended)
    async with StakeAPI(api_key=api_key) as client:
        try:
            # Get user profile
            print("Getting user profile...")
            user = await client.get_user_profile()
            print(f"Welcome, {user.username}!")
            print(f"Account verified: {user.verified}")
            print(f"Default currency: {user.currency}")
            
            # Get account balance
            print("\nGetting account balance...")
            balance = await client.get_user_balance()
            for currency, amount in balance.items():
                print(f"{currency}: {amount}")
            
            # Get casino games
            print("\nGetting casino games...")
            games = await client.get_casino_games(category="slots")
            print(f"Found {len(games)} slot games")
            
            # Show first 5 games
            for game in games[:5]:
                print(f"- {game.name} by {game.provider}")
                print(f"  Min bet: {game.min_bet}, Max bet: {game.max_bet}")
                if game.rtp:
                    print(f"  RTP: {game.rtp}%")
            
            # Get sports events
            print("\nGetting sports events...")
            events = await client.get_sports_events(sport="football")
            print(f"Found {len(events)} football events")
            
            # Show upcoming events
            for event in events[:3]:
                print(f"- {event.home_team} vs {event.away_team}")
                print(f"  League: {event.league}")
                print(f"  Start time: {event.start_time}")
                if event.odds:
                    print(f"  Odds - Home: {event.odds.get('home', 'N/A')}")
            
            # Get bet history
            print("\nGetting bet history...")
            bets = await client.get_bet_history(limit=10)
            print(f"Found {len(bets)} recent bets")
            
            total_wagered = sum(bet.amount for bet in bets)
            print(f"Total wagered in last 10 bets: {total_wagered}")
            
        except AuthenticationError:
            print("Authentication failed. Please check your API key.")
        except StakeAPIError as e:
            print(f"API error occurred: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


async def game_search_example():
    """Demonstrate searching for specific games."""
    
    api_key = os.getenv("STAKE_API_KEY")
    if not api_key:
        print("Please set STAKE_API_KEY environment variable")
        return
    
    async with StakeAPI(api_key=api_key) as client:
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
    
    api_key = os.getenv("STAKE_API_KEY")
    if not api_key:
        print("Please set STAKE_API_KEY environment variable")
        return
    
    async with StakeAPI(api_key=api_key) as client:
        try:
            # Check balance first
            balance = await client.get_user_balance()
            usd_balance = balance.get("USD", 0)
            
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
