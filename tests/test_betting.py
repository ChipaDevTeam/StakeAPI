"""Tests for the betting methods and their safeguards (nothing is sent)."""

import pytest
from unittest.mock import patch

from stakeapi import StakeAPI
from stakeapi.exceptions import BettingDisabledError, PermissionDeniedError, ValidationError


@pytest.fixture
async def betting_client():
    client = StakeAPI(access_token="tok", allow_betting=True)
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_betting_disabled_by_default(stake_client):
    with patch.object(stake_client, '_request') as mock_request:
        with pytest.raises(BettingDisabledError):
            await stake_client.dice_roll(0.001, "btc", target=50.5)
        with pytest.raises(BettingDisabledError):
            await stake_client.crash_bet(0.001, "btc", cashout_at=2)
    mock_request.assert_not_called()


@pytest.mark.asyncio
async def test_dry_run_returns_request_without_sending(stake_client):
    with patch.object(stake_client, '_request') as mock_request:
        dice = await stake_client.dice_roll(0.001, "btc", target=50.5, condition="below", dry_run=True)
        crash = await stake_client.crash_bet(0.001, "btc", cashout_at=2, dry_run=True)
    mock_request.assert_not_called()
    assert dice["endpoint"] == "/_api/casino/dice/roll"
    assert dice["variables"]["condition"] == "below"
    assert dice["variables"]["identifier"]
    assert crash == {
        "dry_run": True,
        "endpoint": "/_api/graphql",
        "operation_name": "MultiplayerCrashBet",
        "variables": {"amount": 0.001, "currency": "btc", "cashoutAt": 2},
    }


@pytest.mark.asyncio
async def test_dice_roll_posts_json_and_unwraps_result(betting_client):
    response = {"diceRoll": {"id": "b1", "amount": 0.001, "payout": 0.00198}}
    with patch.object(betting_client, '_request', return_value=response) as mock_request:
        result = await betting_client.dice_roll(0.001, "btc", target=50.5)
    assert result["id"] == "b1"
    method, endpoint = mock_request.call_args.args
    body = mock_request.call_args.kwargs["data"]
    assert (method, endpoint) == ("POST", "/_api/casino/dice/roll")
    assert body["target"] == 50.5 and body["amount"] == 0.001 and body["currency"] == "btc"


@pytest.mark.asyncio
async def test_casino_bet_maps_errors(betting_client):
    response = {"errors": [{"message": "Please log in.", "errorType": "notAuthenticated"}]}
    with patch.object(betting_client, '_request', return_value=response):
        with pytest.raises(PermissionDeniedError):
            await betting_client.casino_bet("limbo/bet", {"amount": 0, "currency": "btc"})


@pytest.mark.asyncio
async def test_sport_bet_drops_unset_variables(betting_client):
    data = {"sportBet": {"id": "s1"}}
    with patch.object(betting_client, '_graphql_request', return_value=data) as mock_gql:
        result = await betting_client.place_sport_bet(
            1.0, "usdt", ["o1", "o2"], odds_change="x", bet_type="y", identifier="id1"
        )
    assert result == {"id": "s1"}
    assert mock_gql.call_args.kwargs["variables"] == {
        "amount": 1.0, "currency": "usdt", "outcomeIds": ["o1", "o2"],
        "oddsChange": "x", "betType": "y", "identifier": "id1",
    }
    assert mock_gql.call_args.kwargs["operation_name"] == "BetSlipFooter_SportBet"


@pytest.mark.asyncio
@pytest.mark.parametrize("call", [
    lambda c: c.dice_roll(-1, "btc", target=50),
    lambda c: c.dice_roll(1, "btc", target=99),
    lambda c: c.dice_roll(1, "btc", target=50, condition="sideways"),
    lambda c: c.crash_bet(1, "btc", cashout_at=1),
    lambda c: c.place_sport_bet(1, "btc", [], odds_change="x", bet_type="y"),
    lambda c: c.dice_roll(1, "", target=50),
])
async def test_invalid_bets_rejected_before_sending(betting_client, call):
    with patch.object(betting_client, '_request') as mock_request:
        with pytest.raises(ValidationError):
            await call(betting_client)
    mock_request.assert_not_called()


@pytest.mark.asyncio
async def test_place_bet_points_to_per_game_methods(stake_client):
    with pytest.raises(Exception, match="dice_roll"):
        await stake_client.place_bet({})
