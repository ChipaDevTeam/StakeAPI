"""Tests for StakeAPI client."""

import pytest
from unittest.mock import patch
from stakeapi import StakeAPI
from stakeapi.exceptions import AuthenticationError, RateLimitError, StakeAPIError
from stakeapi.models import User, Game, SportEvent


# Trimmed copies of real responses from the live API
KURATOR_GAME = {
    "id": "4f37771e-8270-4afb-966c-a6dd8f9c0a6f",
    "name": "dice",
    "slug": "stake-dice",
    "type": "stake",
    "description": "game_kurator_game_description.stake_dice",
    "edge": 0.01,
    "thumbnailUrl": "https://mediumrare.imgix.net/edfa399c",
    "playerCount": 2765,
    "providerGroup": {"id": "dd7f", "name": "Stake Originals", "slug": "stake-originals"},
    "groupGames": [
        {"group": {"id": "598f", "slug": "dice", "translation": "Dice", "type": "theme"}},
        {"group": {"id": "ee92", "slug": "provably-fair", "translation": "Provably Fair", "type": "category"}},
    ],
}

FIXTURE = {
    "id": "0e40524a-ab7e-4754-a943-1b49f898cb5a",
    "status": "active",
    "name": "Smith, Michael - van Schie, Jimmy",
    "data": {
        "__typename": "SportFixtureDataMatch",
        "startTime": "Wed, 28 Oct 2026 12:50:00 GMT",
        "teams": [
            {"name": "Smith, Michael", "qualifier": "home"},
            {"name": "van Schie, Jimmy", "qualifier": "away"},
        ],
    },
    "groups": [{"templates": [{"markets": [{"outcomes": [
        {"name": "Smith, Michael", "odds": 1.4, "active": True},
        {"name": "van Schie, Jimmy", "odds": 2.85, "active": True},
    ]}]}]}],
}


class TestStakeAPI:
    """Test cases for StakeAPI client."""

    def test_init(self, access_token):
        """Test client initialization."""
        client = StakeAPI(access_token=access_token)
        assert client.access_token == access_token
        assert client.base_url == "https://stake.com"
        assert client.timeout == 30
        assert client.rate_limit == 10

    def test_init_with_custom_params(self):
        """Test client initialization with custom parameters."""
        client = StakeAPI(
            access_token="test",
            base_url="https://stake1017.com",
            timeout=60,
            rate_limit=5,
        )
        assert client.base_url == "https://stake1017.com"
        assert client.timeout == 60
        assert client.rate_limit == 5

    @pytest.mark.asyncio
    async def test_context_manager(self, access_token):
        """Test client as async context manager."""
        async with StakeAPI(access_token=access_token) as client:
            assert client._session is not None

    @pytest.mark.asyncio
    async def test_authentication_error(self, stake_client):
        """Test authentication error handling."""
        with patch.object(stake_client, '_request', side_effect=AuthenticationError("Invalid token")):
            with pytest.raises(AuthenticationError):
                await stake_client.get_user_profile()

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, stake_client):
        """Test rate limit error handling."""
        with patch.object(stake_client, '_request', side_effect=RateLimitError("Rate limit exceeded")):
            with pytest.raises(RateLimitError):
                await stake_client.get_casino_games()

    @pytest.mark.asyncio
    async def test_get_casino_games(self, stake_client):
        """Test getting casino games from a lobby group."""
        data = {"slugKuratorGroup": {"groupGamesList": [{"game": KURATOR_GAME}]}}
        with patch.object(stake_client, '_graphql_request', return_value=data) as mock_gql:
            games = await stake_client.get_casino_games(category="stake-originals")

        assert mock_gql.call_args.kwargs["variables"]["slug"] == "stake-originals"
        assert len(games) == 1
        game = games[0]
        assert isinstance(game, Game)
        assert game.slug == "stake-dice"
        assert game.provider == "Stake Originals"
        assert game.category == "Provably Fair"
        assert game.rtp == 99.0
        assert game.player_count == 2765

    @pytest.mark.asyncio
    async def test_get_casino_games_unknown_group(self, stake_client):
        """Test an unknown lobby group raises."""
        with patch.object(stake_client, '_graphql_request', return_value={"slugKuratorGroup": None}):
            with pytest.raises(StakeAPIError):
                await stake_client.get_casino_games(category="nope")

    @pytest.mark.asyncio
    async def test_get_game_details(self, stake_client):
        """Test getting one game by slug."""
        with patch.object(stake_client, '_graphql_request', return_value={"slugKuratorGame": KURATOR_GAME}):
            game = await stake_client.get_game_details("stake-dice")
        assert game.name == "dice"

    @pytest.mark.asyncio
    async def test_get_user_profile(self, stake_client):
        """Test getting user profile."""
        data = {"user": {
            "id": "u1", "name": "testuser", "email": "t@example.com",
            "hasEmailVerified": True, "createdAt": "Sat, 11 Jul 2026 07:41:10 GMT",
        }}
        with patch.object(stake_client, '_graphql_request', return_value=data):
            user = await stake_client.get_user_profile()

        assert isinstance(user, User)
        assert user.username == "testuser"
        assert user.verified is True

    @pytest.mark.asyncio
    async def test_get_sports_events(self, stake_client):
        """Test sports events are mapped from the SportIndex query."""
        data = {"slugSport": {
            "name": "Darts",
            "firstTournament": [{"name": "PDC Players Championship", "fixtureList": [FIXTURE]}],
        }}
        with patch.object(stake_client, '_graphql_request', return_value=data):
            events = await stake_client.get_sports_events("darts")

        assert len(events) == 1
        event = events[0]
        assert isinstance(event, SportEvent)
        assert event.home_team == "Smith, Michael"
        assert event.away_team == "van Schie, Jimmy"
        assert event.league == "PDC Players Championship"
        assert event.odds == {"Smith, Michael": 1.4, "van Schie, Jimmy": 2.85}

    @pytest.mark.asyncio
    async def test_get_fixtures(self, stake_client):
        """Test fixture list returns the count and fixtures."""
        data = {"fixtureCount": 1723, "fixtureList": [FIXTURE]}
        with patch.object(stake_client, '_graphql_request', return_value=data):
            result = await stake_client.get_fixtures(limit=1)
        assert result == {"count": 1723, "fixtures": [FIXTURE]}

    @pytest.mark.asyncio
    async def test_search_sports_skips_empty_results(self, stake_client):
        """Test non-fixture search results are dropped."""
        data = {"sportFixtureQuery": [{"fixture": FIXTURE}, {"fixture": {}}]}
        with patch.object(stake_client, '_graphql_request', return_value=data):
            fixtures = await stake_client.search_sports("smith")
        assert fixtures == [FIXTURE]

    @pytest.mark.asyncio
    async def test_get_currency_limits(self, stake_client):
        """Test currency limits are parsed to floats."""
        data = {"info": {"currencies": [
            {"name": "btc", "betMax": {"value": "100"}, "betMaxProfit": {"value": "10"}},
            {"name": "usdt", "betMax": None, "betMaxProfit": {"value": "1000"}},
        ]}}
        with patch.object(stake_client, '_graphql_request', return_value=data):
            limits = await stake_client.get_currency_limits()
        assert limits == {
            "btc": {"bet_max": 100.0, "bet_max_profit": 10.0},
            "usdt": {"bet_max": None, "bet_max_profit": 1000.0},
        }

    @pytest.mark.asyncio
    async def test_get_game_payouts(self, stake_client):
        """Test payout tables are split per game."""
        data = {"info": {
            "kenoPayouts": [{"payouts": [0, 3.96], "risk": "classic"}],
            "plinkoPayouts": [{"payouts": [5.6, 2.1], "rows": 8, "risk": "low"}],
            "wheelPayouts": None,
        }}
        with patch.object(stake_client, '_graphql_request', return_value=data):
            payouts = await stake_client.get_game_payouts()
        assert payouts["keno"][0]["risk"] == "classic"
        assert payouts["plinko"][0]["rows"] == 8
        assert payouts["wheel"] == []
