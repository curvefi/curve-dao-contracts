import math

import brownie
import pytest

DAY = 86400


@pytest.fixture(scope="module", autouse=True)
def local_setup(alice, bob, charlie, chain, coin_reward, child_chain_streamer):
    coin_reward._mint_for_testing(100 * 10 ** 18, {"from": alice})
    coin_reward.transfer(child_chain_streamer, 100 * 10 ** 18, {"from": alice})

    child_chain_streamer.add_reward(coin_reward, charlie, DAY * 14, {"from": alice})
    child_chain_streamer.set_receiver(bob, {"from": alice})


def test_only_distributor(alice, charlie, coin_reward, child_chain_streamer):
    with brownie.reverts("dev: only distributor"):
        child_chain_streamer.notify_reward_amount(coin_reward, {"from": alice})

    child_chain_streamer.notify_reward_amount(coin_reward, {"from": charlie})


def test_available_rewards_are_distributed(charlie, bob, chain, coin_reward, child_chain_streamer):

    child_chain_streamer.notify_reward_amount(coin_reward, {"from": charlie})

    chain.mine(timedelta=DAY * 7)

    child_chain_streamer.notify_reward_amount(coin_reward, {"from": charlie})

    assert math.isclose(coin_reward.balanceOf(bob), 50 * 10 ** 18, rel_tol=0.00001)


def test_increase_reward_amount_mid_distribution(
    alice, chain, charlie, coin_reward, child_chain_streamer
):
    child_chain_streamer.notify_reward_amount(coin_reward, {"from": charlie})
    chain.mine(timedelta=DAY * 7)  # half the rewards have been streamed
    coin_reward._mint_for_testing(100 * 10 ** 18, {"from": alice})  # give another 100
    # approx 50 will be distributed in this call leaving 150 behind over the course of 14 days

    coin_reward.transfer(child_chain_streamer, 100 * 10 ** 18, {"from": alice})
    tx = child_chain_streamer.notify_reward_amount(coin_reward, {"from": charlie})
    data = child_chain_streamer.reward_data(coin_reward)

    expected_rate = (50 + 100) * 10 ** 18 // (14 * DAY)

    assert data["period_finish"] == tx.timestamp + 14 * DAY
    assert data["received"] == 200 * 10 ** 18
    assert math.isclose(data["rate"], expected_rate, rel_tol=0.00001)
