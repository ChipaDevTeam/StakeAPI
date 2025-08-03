"""Tests for utility functions."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from stakeapi.utils import (
    validate_api_key,
    safe_decimal,
    parse_datetime,
    format_currency,
    calculate_win_rate,
    validate_bet_amount,
    sanitize_game_name
)


class TestValidateApiKey:
    """Test cases for API key validation."""
    
    def test_valid_api_key(self):
        """Test valid API key."""
        valid_key = "a" * 32  # 32 character string
        assert validate_api_key(valid_key) is True
        
    def test_invalid_api_key_too_short(self):
        """Test invalid API key - too short."""
        short_key = "a" * 16
        assert validate_api_key(short_key) is False
        
    def test_invalid_api_key_special_chars(self):
        """Test invalid API key with special characters."""
        invalid_key = "a" * 30 + "!@"
        assert validate_api_key(invalid_key) is False
        
    def test_empty_api_key(self):
        """Test empty API key."""
        assert validate_api_key("") is False
        assert validate_api_key(None) is False


class TestSafeDecimal:
    """Test cases for safe decimal conversion."""
    
    def test_valid_decimal_string(self):
        """Test valid decimal string."""
        result = safe_decimal("10.50")
        assert result == Decimal("10.50")
        
    def test_valid_decimal_number(self):
        """Test valid decimal number."""
        result = safe_decimal(10.50)
        assert result == Decimal("10.50")
        
    def test_invalid_decimal(self):
        """Test invalid decimal value."""
        assert safe_decimal("invalid") is None
        assert safe_decimal(None) is None
        assert safe_decimal([]) is None


class TestParseDatetime:
    """Test cases for datetime parsing."""
    
    def test_iso_format_with_z(self):
        """Test ISO format with Z timezone."""
        date_str = "2025-01-01T12:00:00Z"
        result = parse_datetime(date_str)
        
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1
        
    def test_iso_format_with_timezone(self):
        """Test ISO format with timezone offset."""
        date_str = "2025-01-01T12:00:00+00:00"
        result = parse_datetime(date_str)
        
        assert result is not None
        assert result.tzinfo is not None
        
    def test_invalid_datetime(self):
        """Test invalid datetime string."""
        assert parse_datetime("invalid-date") is None
        assert parse_datetime("") is None
        assert parse_datetime(None) is None


class TestFormatCurrency:
    """Test cases for currency formatting."""
    
    def test_usd_formatting(self):
        """Test USD formatting."""
        amount = Decimal("123.45")
        result = format_currency(amount, "USD")
        assert result == "$123.45"
        
    def test_eur_formatting(self):
        """Test EUR formatting."""
        amount = Decimal("100.00")
        result = format_currency(amount, "EUR")
        assert result == "€100.00"
        
    def test_unknown_currency(self):
        """Test unknown currency formatting."""
        amount = Decimal("50.75")
        result = format_currency(amount, "XYZ")
        assert result == "50.75 XYZ"


class TestCalculateWinRate:
    """Test cases for win rate calculation."""
    
    def test_normal_win_rate(self):
        """Test normal win rate calculation."""
        win_rate = calculate_win_rate(80, 100)
        assert win_rate == 80.0
        
    def test_zero_bets(self):
        """Test win rate with zero bets."""
        win_rate = calculate_win_rate(0, 0)
        assert win_rate == 0.0
        
    def test_partial_win_rate(self):
        """Test partial win rate."""
        win_rate = calculate_win_rate(33, 100)
        assert win_rate == 33.0


class TestValidateBetAmount:
    """Test cases for bet amount validation."""
    
    def test_valid_bet_amount(self):
        """Test valid bet amount."""
        amount = Decimal("10.00")
        min_bet = Decimal("1.00")
        max_bet = Decimal("100.00")
        
        assert validate_bet_amount(amount, min_bet, max_bet) is True
        
    def test_bet_amount_too_low(self):
        """Test bet amount below minimum."""
        amount = Decimal("0.50")
        min_bet = Decimal("1.00")
        max_bet = Decimal("100.00")
        
        assert validate_bet_amount(amount, min_bet, max_bet) is False
        
    def test_bet_amount_too_high(self):
        """Test bet amount above maximum."""
        amount = Decimal("150.00")
        min_bet = Decimal("1.00")
        max_bet = Decimal("100.00")
        
        assert validate_bet_amount(amount, min_bet, max_bet) is False


class TestSanitizeGameName:
    """Test cases for game name sanitization."""
    
    def test_normal_game_name(self):
        """Test normal game name."""
        name = "Mega Slots Deluxe"
        result = sanitize_game_name(name)
        assert result == "Mega Slots Deluxe"
        
    def test_game_name_with_special_chars(self):
        """Test game name with special characters."""
        name = "Super Game! @#$% Edition"
        result = sanitize_game_name(name)
        assert result == "Super Game  Edition"
        
    def test_empty_game_name(self):
        """Test empty game name."""
        assert sanitize_game_name("") == ""
        assert sanitize_game_name(None) == ""
