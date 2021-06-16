import brownie
import pytest
from brownie import ZERO_ADDRESS

DAY = 86400


@pytest.fixture(scope="module", autouse=True)
def local_setup(alice, charlie, coin_reward, child_chain_streamer):
    coin_reward._mint_for_testing(alice, 100 * 10 ** 18)
    coin_reward.transfer(child_chain_streamer, 100 * 10 ** 18, {"from": alice})


def test_admin_only(charlie, child_chain_streamer, coin_reward):
    with brownie.reverts("dev: only owner"):
        child_chain_streamer.remove_reward(coin_reward, {"from": charlie})


def test_reward_not_active(alice, child_chain_streamer, token):
    with brownie.reverts("Reward token not added"):
        child_chain_streamer.remove_reward(token, {"from": alice})


def test_returns_reward_to_owner(alice, child_chain_streamer, coin_reward):
    child_chain_streamer.remove_reward(coin_reward, {"from": alice})

    assert coin_reward.balanceOf(alice) == 100 * 10 ** 18


def test_reward_data_cleared(alice, child_chain_streamer, coin_reward):
    child_chain_streamer.remove_reward(coin_reward, {"from": alice})

    assert child_chain_streamer.reward_data(coin_reward) == (ZERO_ADDRESS, 0, 0, 0, 0, 0)


def test_reward_indexes_corrected(alice, child_chain_streamer, token, coin_reward):
    child_chain_streamer.add_reward(token, alice, DAY * 18, {"from": alice})
    child_chain_streamer.remove_reward(coin_reward, {"from": alice})

    child_chain_streamer.reward_tokens(0) == token
