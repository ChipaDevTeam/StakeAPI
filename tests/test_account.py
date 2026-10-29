"""Tests for the logged-in account methods."""

import pytest
from unittest.mock import patch

from stakeapi.exceptions import PermissionDeniedError, StakeAPIError
from stakeapi.models import Game


def gql(stake_client, data):
    return patch.object(stake_client, '_graphql_request', return_value=data)


@pytest.mark.asyncio
async def test_user_stats_is_public(stake_client):
    data = {"user": {"id": "u1", "name": "beeeen10", "statisticScoped": None}}
    with gql(stake_client, data) as mock_gql:
        user = await stake_client.get_user_stats("beeeen10")
    assert user["name"] == "beeeen10"
    assert mock_gql.call_args.kwargs["variables"] == {"name": "beeeen10"}


@pytest.mark.asyncio
async def test_user_stats_unknown_user(stake_client):
    with gql(stake_client, {"user": None}):
        with pytest.raises(StakeAPIError):
            await stake_client.get_user_stats("nobody")


@pytest.mark.asyncio
async def test_missing_user_means_expired_session(stake_client):
    with gql(stake_client, {"user": None}):
        with pytest.raises(StakeAPIError, match="session may have expired"):
            await stake_client.get_vip_info()


@pytest.mark.asyncio
async def test_seed_pair_is_flattened(stake_client):
    data = {"user": {
        "activeClientSeed": {"id": "c", "seed": "my-seed"},
        "activeServerSeed": {"id": "s", "nonce": 42, "seedHash": "abc", "nextSeedHash": "def"},
        "activeCasinoBets": [],
    }}
    with gql(stake_client, data):
        seeds = await stake_client.get_seed_pair()
    assert seeds == {
        "client_seed": "my-seed",
        "server_seed_hash": "abc",
        "next_server_seed_hash": "def",
        "nonce": 42,
        "active_bets": [],
    }


@pytest.mark.asyncio
async def test_sport_bet_history_keeps_sport_bets_only(stake_client):
    data = {"user": {"sportBetList": [
        {"iid": "sport:1", "bet": {"__typename": "SportBet", "id": "b1", "amount": 5}},
        {"iid": "racing:2", "bet": {"__typename": "RacingBet", "id": "b2"}},
        {"iid": "sport:3", "bet": None},
    ]}}
    with gql(stake_client, data) as mock_gql:
        bets = await stake_client.get_sport_bet_history(status=["settled"])
    assert bets == [{"iid": "sport:1", "__typename": "SportBet", "id": "b1", "amount": 5}]
    assert mock_gql.call_args.kwargs["variables"]["status"] == ["settled"]


@pytest.mark.asyncio
async def test_tip_history_looks_up_own_name(stake_client):
    responses = [
        {"user": {"id": "u1", "name": "me"}},
        {"user": {"id": "u1", "tipHistory": [{"id": "t1", "amount": 1}]}},
    ]
    with patch.object(stake_client, '_graphql_request', side_effect=responses) as mock_gql:
        tips = await stake_client.get_tip_history()
    assert tips == [{"id": "t1", "amount": 1}]
    assert mock_gql.call_args.kwargs["variables"]["name"] == "me"


@pytest.mark.asyncio
async def test_favourite_games_are_game_models(stake_client):
    data = {"user": {"favouriteGameList": [
        {"id": "g1", "name": "dice", "slug": "stake-dice", "edge": 0.01,
         "providerGroup": {"name": "Stake Originals"}, "groupGames": []},
    ]}}
    with gql(stake_client, data):
        games = await stake_client.get_favourite_games()
    assert isinstance(games[0], Game)
    assert games[0].provider == "Stake Originals"


@pytest.mark.asyncio
async def test_bet_history_game_filter(stake_client):
    with gql(stake_client, {"user": {"houseBetList": []}}) as mock_gql:
        await stake_client.get_bet_history(game="dice")
    assert mock_gql.call_args.kwargs["variables"]["game"] == "dice"


@pytest.mark.asyncio
async def test_please_log_in_raises_permission_denied(stake_client):
    response = {"data": None, "errors": [
        {"message": "Please log in.", "errorType": "notAuthenticated"}
    ]}
    with patch.object(stake_client, '_request', return_value=response):
        with pytest.raises(PermissionDeniedError):
            await stake_client.get_claimable_bonuses()
