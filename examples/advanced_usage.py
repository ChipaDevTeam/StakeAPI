"""
Advanced examples for StakeAPI.

This script demonstrates advanced features like WebSocket connections,
batch operations, and custom error handling.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from stakeapi import StakeAPI
from stakeapi.models import Game, SportEvent
from stakeapi.exceptions import StakeAPIError


class StakeAnalytics:
    """Advanced analytics using StakeAPI."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def analyze_games_by_provider(self) -> Dict[str, Dict[str, Any]]:
        """Analyze games grouped by provider."""
        async with StakeAPI(api_key=self.api_key) as client:
            games = await client.get_casino_games()
            
            provider_stats = {}
            for game in games:
                provider = game.provider
                if provider not in provider_stats:
                    provider_stats[provider] = {
                        "game_count": 0,
                        "categories": set(),
                        "avg_rtp": [],
                        "min_bet_range": [],
                        "max_bet_range": []
                    }
                
                stats = provider_stats[provider]
                stats["game_count"] += 1
                stats["categories"].add(game.category)
                
                if game.rtp:
                    stats["avg_rtp"].append(game.rtp)
                stats["min_bet_range"].append(float(game.min_bet))
                stats["max_bet_range"].append(float(game.max_bet))
            
            # Calculate averages
            for provider, stats in provider_stats.items():
                stats["categories"] = list(stats["categories"])
                if stats["avg_rtp"]:
                    stats["avg_rtp"] = sum(stats["avg_rtp"]) / len(stats["avg_rtp"])
                else:
                    stats["avg_rtp"] = None
                    
                stats["min_bet_avg"] = sum(stats["min_bet_range"]) / len(stats["min_bet_range"])
                stats["max_bet_avg"] = sum(stats["max_bet_range"]) / len(stats["max_bet_range"])
                
                # Clean up temporary lists
                del stats["min_bet_range"]
                del stats["max_bet_range"]
            
            return provider_stats
    
    async def find_best_odds_events(self, sport: str = None) -> List[SportEvent]:
        """Find sports events with the best odds."""
        async with StakeAPI(api_key=self.api_key) as client:
            events = await client.get_sports_events(sport=sport)
            
            # Filter events with odds and sort by potential value
            events_with_odds = [e for e in events if e.odds]
            
            # Calculate implied probability and find value bets
            valuable_events = []
            for event in events_with_odds:
                if "home" in event.odds and "away" in event.odds:
                    home_prob = 1 / event.odds["home"]
                    away_prob = 1 / event.odds["away"]
                    total_prob = home_prob + away_prob
                    
                    # Look for events where bookmaker margin is low
                    if total_prob < 1.05:  # Less than 5% margin
                        valuable_events.append(event)
            
            return valuable_events
    
    async def get_user_performance_stats(self) -> Dict[str, Any]:
        """Analyze user betting performance."""
        async with StakeAPI(api_key=self.api_key) as client:
            bets = await client.get_bet_history(limit=100)
            
            if not bets:
                return {"message": "No betting history found"}
            
            total_bets = len(bets)
            won_bets = [b for b in bets if b.status == "won"]
            lost_bets = [b for b in bets if b.status == "lost"]
            
            total_wagered = sum(bet.amount for bet in bets)
            total_won = sum(bet.potential_payout for bet in won_bets)
            total_lost = sum(bet.amount for bet in lost_bets)
            
            win_rate = len(won_bets) / total_bets * 100 if total_bets > 0 else 0
            roi = ((total_won - total_wagered) / total_wagered * 100) if total_wagered > 0 else 0
            
            # Find most profitable game/event
            game_profits = {}
            for bet in bets:
                game_id = bet.game_id or bet.event_id
                if game_id:
                    if game_id not in game_profits:
                        game_profits[game_id] = {"profit": 0, "bets": 0}
                    
                    if bet.status == "won":
                        game_profits[game_id]["profit"] += float(bet.potential_payout - bet.amount)
                    elif bet.status == "lost":
                        game_profits[game_id]["profit"] -= float(bet.amount)
                    
                    game_profits[game_id]["bets"] += 1
            
            most_profitable = max(game_profits.items(), key=lambda x: x[1]["profit"]) if game_profits else None
            
            return {
                "total_bets": total_bets,
                "win_rate": round(win_rate, 2),
                "total_wagered": float(total_wagered),
                "total_won": float(total_won),
                "net_profit": float(total_won - total_wagered),
                "roi_percentage": round(roi, 2),
                "most_profitable_game": most_profitable[0] if most_profitable else None,
                "most_profitable_profit": most_profitable[1]["profit"] if most_profitable else 0
            }


async def batch_game_analysis():
    """Perform batch analysis of all games."""
    api_key = os.getenv("STAKE_API_KEY")
    if not api_key:
        print("Please set STAKE_API_KEY environment variable")
        return
    
    analytics = StakeAnalytics(api_key)
    
    print("Analyzing games by provider...")
    provider_stats = await analytics.analyze_games_by_provider()
    
    print("\n=== Provider Analysis ===")
    for provider, stats in sorted(provider_stats.items(), key=lambda x: x[1]["game_count"], reverse=True)[:10]:
        print(f"\n{provider}:")
        print(f"  Games: {stats['game_count']}")
        print(f"  Categories: {', '.join(stats['categories'])}")
        if stats['avg_rtp']:
            print(f"  Average RTP: {stats['avg_rtp']:.2f}%")
        print(f"  Avg Min Bet: ${stats['min_bet_avg']:.2f}")
        print(f"  Avg Max Bet: ${stats['max_bet_avg']:.2f}")


async def live_odds_monitoring():
    """Monitor live odds changes (simulated)."""
    api_key = os.getenv("STAKE_API_KEY")
    if not api_key:
        print("Please set STAKE_API_KEY environment variable")
        return
    
    analytics = StakeAnalytics(api_key)
    
    print("Finding events with best odds...")
    valuable_events = await analytics.find_best_odds_events(sport="football")
    
    print(f"\n=== Value Betting Opportunities ===")
    print(f"Found {len(valuable_events)} events with low bookmaker margins:")
    
    for event in valuable_events[:5]:
        print(f"\n{event.home_team} vs {event.away_team}")
        print(f"League: {event.league}")
        print(f"Start: {event.start_time}")
        print(f"Odds - Home: {event.odds.get('home')}, Away: {event.odds.get('away')}")
        
        # Calculate implied probabilities
        home_prob = (1 / event.odds["home"]) * 100
        away_prob = (1 / event.odds["away"]) * 100
        margin = home_prob + away_prob - 100
        print(f"Bookmaker margin: {margin:.2f}%")


async def performance_dashboard():
    """Display user performance dashboard."""
    api_key = os.getenv("STAKE_API_KEY")
    if not api_key:
        print("Please set STAKE_API_KEY environment variable")
        return
    
    analytics = StakeAnalytics(api_key)
    
    print("Analyzing your betting performance...")
    stats = await analytics.get_user_performance_stats()
    
    print("\n=== Your Performance Dashboard ===")
    if "message" in stats:
        print(stats["message"])
        return
    
    print(f"Total Bets: {stats['total_bets']}")
    print(f"Win Rate: {stats['win_rate']}%")
    print(f"Total Wagered: ${stats['total_wagered']:.2f}")
    print(f"Total Won: ${stats['total_won']:.2f}")
    print(f"Net Profit: ${stats['net_profit']:.2f}")
    print(f"ROI: {stats['roi_percentage']}%")
    
    if stats['most_profitable_game']:
        print(f"\nMost Profitable Game: {stats['most_profitable_game']}")
        print(f"Profit from this game: ${stats['most_profitable_profit']:.2f}")


async def error_handling_example():
    """Demonstrate comprehensive error handling."""
    api_key = os.getenv("STAKE_API_KEY")
    if not api_key:
        print("Please set STAKE_API_KEY environment variable")
        return
    
    # Custom retry logic
    async def retry_request(func, max_retries=3, delay=1):
        """Retry function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return await func()
            except StakeAPIError as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(delay * (2 ** attempt))
    
    async with StakeAPI(api_key=api_key) as client:
        try:
            # Retry getting user profile
            user = await retry_request(client.get_user_profile)
            print(f"Successfully got profile for {user.username}")
            
        except StakeAPIError as e:
            print(f"Failed after retries: {e}")


async def main():
    """Run advanced examples."""
    print("=== Advanced StakeAPI Examples ===\n")
    
    examples = [
        ("Batch Game Analysis", batch_game_analysis),
        ("Live Odds Monitoring", live_odds_monitoring),
        ("Performance Dashboard", performance_dashboard),
        ("Error Handling Example", error_handling_example),
    ]
    
    for name, func in examples:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            await func()
        except Exception as e:
            print(f"Error in {name}: {e}")
        
        print("\n" + "="*60)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    asyncio.run(main())
