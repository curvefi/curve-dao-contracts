import math

import brownie
import pytest

DAY = 86400


@pytest.fixture(scope="module", autouse=True)
def local_setup(alice, bob, charlie, coin_reward, child_chain_streamer):
    coin_reward._mint_for_testing(100 * 10 ** 18, {"from": alice})
    coin_reward.transfer(child_chain_streamer, 100 * 10 ** 18, {"from": alice})
    child_chain_streamer.add_reward(coin_reward, charlie, DAY * 7, {"from": alice})
    child_chain_streamer.set_receiver(bob, {"from": alice})
    child_chain_streamer.notify_reward_amount(coin_reward, {"from": charlie})


def test_receiver_only(alice, child_chain_streamer):
    with brownie.reverts("Caller is not receiver"):
        child_chain_streamer.get_reward({"from": alice})


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
