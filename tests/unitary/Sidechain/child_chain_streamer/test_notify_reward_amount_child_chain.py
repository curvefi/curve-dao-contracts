import math

import brownie
import pytest

DAY = 86400


@pytest.fixture(scope="module", autouse=True)
def local_setup(alice, bob, charlie, chain, coin_reward, child_chain_streamer):
    coin_reward._mint_for_testing(alice, 100 * 10 ** 18)
    coin_reward.transfer(child_chain_streamer, 100 * 10 ** 18, {"from": alice})


@pytest.mark.parametrize("idx", range(5))
def test_unguarded(accounts, coin_reward, child_chain_streamer, idx):
    child_chain_streamer.notify_reward_amount(coin_reward, {"from": accounts[idx]})


def test_only_updates(charlie, bob, chain, coin_reward, child_chain_streamer):

    child_chain_streamer.notify_reward_amount(coin_reward, {"from": charlie})

    chain.mine(timedelta=DAY * 7)

    with brownie.reverts("Invalid token or no new reward"):
        child_chain_streamer.notify_reward_amount(coin_reward, {"from": charlie})


def test_increase_reward_amount_mid_distribution(
    alice, chain, charlie, coin_reward, child_chain_streamer
):
    child_chain_streamer.notify_reward_amount(coin_reward, {"from": charlie})
    chain.mine(timedelta=DAY * 3.5)  # half the rewards have been streamed
    coin_reward._mint_for_testing(alice, 100 * 10 ** 18)  # give another 100
    # approx 50 will be distributed in this call leaving 150 behind over the course of 14 days

    coin_reward.transfer(child_chain_streamer, 100 * 10 ** 18, {"from": alice})
    # alice has to call notify reward now since she is distributor as owner
    tx = child_chain_streamer.notify_reward_amount(coin_reward, {"from": alice})
    data = child_chain_streamer.reward_data(coin_reward)

    expected_rate = (50 + 100) * 10 ** 18 // (7 * DAY)

    assert data["period_finish"] == tx.timestamp + 7 * DAY
    assert data["received"] == 200 * 10 ** 18
    assert math.isclose(data["rate"], expected_rate, rel_tol=0.00001)


def test_mid_distribution_only_distributor(
    alice, charlie, bob, chain, coin_reward, child_chain_streamer
):
    # Verify that mid distribution of rewards, only the distributor can call
    # notify_reward_amount again, otherwise the period will be extended by a
    # bad actor
    child_chain_streamer.notify_reward_amount(coin_reward, {"from": charlie})

    chain.mine(timedelta=DAY * 3.5)

    # bob gets tokens, then sends them to the streamer hoping to call `notify_reward_amount`
    coin_reward._mint_for_testing(bob, 100 * 10 ** 18)
    coin_reward.transfer(child_chain_streamer, 100 * 10 ** 18, {"from": bob})

    with brownie.reverts("Reward period still active"):
        child_chain_streamer.notify_reward_amount(coin_reward, {"from": bob})
