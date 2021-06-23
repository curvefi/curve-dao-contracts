import math

import pytest
from brownie import ZERO_ADDRESS

REWARD = 10 ** 20
WEEK = 7 * 86400


@pytest.fixture(scope="module")
def reward_contract(RewardStream, alice, charlie, rewards_only_gauge, coin_reward):
    contract = RewardStream.deploy(alice, charlie, coin_reward, 86400 * 7, {"from": alice})
    contract.add_receiver(rewards_only_gauge, {"from": alice})
    coin_reward.approve(contract, 2 ** 256 - 1, {"from": charlie})
    coin_reward._mint_for_testing(charlie, REWARD, {"from": alice})
    return contract


@pytest.fixture(scope="module", autouse=True)
def initial_setup(
    alice,
    charlie,
    chain,
    coin_reward,
    reward_contract,
    token,
    mock_lp_token,
    rewards_only_gauge,
    gauge_controller,
    minter,
):
    # gauge setup
    token.set_minter(minter, {"from": alice})
    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": alice})
    gauge_controller.add_gauge(rewards_only_gauge, 0, 0, {"from": alice})

    # deposit into gauge
    mock_lp_token.approve(rewards_only_gauge, 2 ** 256 - 1, {"from": alice})
    rewards_only_gauge.deposit(10 ** 18, {"from": alice})

    # add rewards
    sigs = reward_contract.get_reward.signature
    rewards_only_gauge.set_rewards(
        reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
    )

    # fund rewards
    reward_contract.notify_reward_amount(REWARD, {"from": charlie})

    # sleep half way through the reward period
    chain.sleep(int(86400 * 3.5))


def test_transfer_does_not_trigger_claim_for_sender(
    alice, bob, chain, rewards_only_gauge, coin_reward
):
    amount = rewards_only_gauge.balanceOf(alice)

    rewards_only_gauge.transfer(bob, amount, {"from": alice})

    reward = coin_reward.balanceOf(alice)
    assert reward == 0


def test_transfer_does_not_trigger_claim_for_receiver(
    alice, bob, chain, rewards_only_gauge, coin_reward
):
    amount = rewards_only_gauge.balanceOf(alice) // 2

    rewards_only_gauge.transfer(bob, amount, {"from": alice})
    chain.sleep(WEEK)
    rewards_only_gauge.transfer(alice, amount, {"from": bob})

    for acct in (alice, bob):
        # rewards_only_gauge.claim_rewards({"from": acct})
        assert coin_reward.balanceOf(acct) == 0


def test_claim_rewards_stil_accurate(alice, bob, chain, rewards_only_gauge, coin_reward):
    amount = rewards_only_gauge.balanceOf(alice)

    rewards_only_gauge.transfer(bob, amount, {"from": alice})

    # sleep half way through the reward period
    chain.sleep(int(86400 * 3.5))

    for acct in (alice, bob):
        rewards_only_gauge.claim_rewards({"from": acct})

        assert math.isclose(coin_reward.balanceOf(acct), REWARD // 2, rel_tol=0.01)
