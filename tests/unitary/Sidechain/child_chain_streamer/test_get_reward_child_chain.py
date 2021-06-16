import math

import pytest

DAY = 86400


@pytest.fixture(scope="module", autouse=True)
def local_setup(alice, bob, charlie, coin_reward, child_chain_streamer):
    coin_reward._mint_for_testing(alice, 100 * 10 ** 18)
    coin_reward.transfer(child_chain_streamer, 100 * 10 ** 18, {"from": alice})
    child_chain_streamer.notify_reward_amount(coin_reward, {"from": charlie})


@pytest.mark.parametrize("idx", range(5))
def test_unguarded(accounts, child_chain_streamer, idx):
    child_chain_streamer.get_reward({"from": accounts[idx]})


def test_last_update_time(bob, chain, child_chain_streamer):
    chain.sleep(1000)
    tx = child_chain_streamer.get_reward({"from": bob})

    assert tx.timestamp == child_chain_streamer.last_update_time()


def test_update_reward(bob, coin_reward, chain, child_chain_streamer):
    chain.mine(timedelta=DAY * 3)
    tx = child_chain_streamer.get_reward({"from": bob})

    assert tx.subcalls[-1]["to"] == coin_reward
    assert tx.subcalls[-1]["function"] == "transfer(address,uint256)"
    assert math.isclose(coin_reward.balanceOf(bob), 3 * 100 * 10 ** 18 // 7, rel_tol=0.0001)
