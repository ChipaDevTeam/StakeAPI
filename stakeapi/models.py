"""Data models for StakeAPI."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal


class User(BaseModel):
    """User model."""
    
    id: str
    username: str
    email: Optional[str] = None
    verified: bool = False
    created_at: datetime
    country: Optional[str] = None
    currency: str = "USD"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create User from dictionary."""
        return cls(**data)


class Game(BaseModel):
    """Casino game model."""
    
    id: str
    name: str
    category: str
    provider: str
    description: Optional[str] = None
    min_bet: Decimal = Field(default=Decimal("0.01"))
    max_bet: Decimal = Field(default=Decimal("1000.00"))
    rtp: Optional[float] = None  # Return to Player percentage
    volatility: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    thumbnail_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Game":
        """Create Game from dictionary."""
        return cls(**data)


class SportEvent(BaseModel):
    """Sports event model."""
    
    id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    start_time: datetime
    status: str
    odds: Dict[str, float] = Field(default_factory=dict)
    live: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SportEvent":
        """Create SportEvent from dictionary."""
        return cls(**data)


class Bet(BaseModel):
    """Bet model."""
    
    id: str
    user_id: str
    game_id: Optional[str] = None
    event_id: Optional[str] = None
    bet_type: str
    amount: Decimal
    potential_payout: Decimal
    odds: Optional[float] = None
    status: str  # pending, won, lost, cancelled
    placed_at: datetime
    settled_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Bet":
        """Create Bet from dictionary."""
        return cls(**data)


class Transaction(BaseModel):
    """Transaction model."""
    
    id: str
    user_id: str
    type: str  # deposit, withdrawal, bet, win
    amount: Decimal
    currency: str
    status: str
    timestamp: datetime
    description: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        """Create Transaction from dictionary."""
        return cls(**data)


class Statistics(BaseModel):
    """User statistics model."""
    
    total_bets: int = 0
    total_wagered: Decimal = Field(default=Decimal("0"))
    total_won: Decimal = Field(default=Decimal("0"))
    total_lost: Decimal = Field(default=Decimal("0"))
    win_rate: float = 0.0
    biggest_win: Decimal = Field(default=Decimal("0"))
    favorite_game: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Statistics":
        """Create Statistics from dictionary."""
        return cls(**data)
