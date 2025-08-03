"""Utility functions for StakeAPI."""

import re
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        True if valid format
    """
    if not api_key or not isinstance(api_key, str):
        return False
        
    # Basic format validation (adjust based on actual format)
    pattern = r'^[a-zA-Z0-9]{32,64}$'
    return bool(re.match(pattern, api_key))


def safe_decimal(value: Any) -> Optional[Decimal]:
    """
    Safely convert value to Decimal.
    
    Args:
        value: Value to convert
        
    Returns:
        Decimal value or None if conversion fails
    """
    if value is None:
        return None
        
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def parse_datetime(date_string: str) -> Optional[datetime]:
    """
    Parse datetime string to datetime object.
    
    Args:
        date_string: ISO format datetime string
        
    Returns:
        Datetime object or None if parsing fails
    """
    if not date_string:
        return None
        
    try:
        # Try parsing ISO format with timezone
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Try parsing without timezone
            dt = datetime.fromisoformat(date_string)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def format_currency(amount: Decimal, currency: str = "USD") -> str:
    """
    Format currency amount for display.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    if currency.upper() == "USD":
        return f"${amount:.2f}"
    elif currency.upper() == "EUR":
        return f"€{amount:.2f}"
    elif currency.upper() == "GBP":
        return f"£{amount:.2f}"
    else:
        return f"{amount:.2f} {currency.upper()}"


def calculate_win_rate(wins: int, total_bets: int) -> float:
    """
    Calculate win rate percentage.
    
    Args:
        wins: Number of wins
        total_bets: Total number of bets
        
    Returns:
        Win rate as percentage (0-100)
    """
    if total_bets == 0:
        return 0.0
        
    return (wins / total_bets) * 100


def validate_bet_amount(amount: Decimal, min_bet: Decimal, max_bet: Decimal) -> bool:
    """
    Validate bet amount is within limits.
    
    Args:
        amount: Bet amount
        min_bet: Minimum bet amount
        max_bet: Maximum bet amount
        
    Returns:
        True if amount is valid
    """
    return min_bet <= amount <= max_bet


def sanitize_game_name(name: str) -> str:
    """
    Sanitize game name for safe usage.
    
    Args:
        name: Game name to sanitize
        
    Returns:
        Sanitized game name
    """
    if not name:
        return ""
        
    # Remove special characters and normalize spaces
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized
