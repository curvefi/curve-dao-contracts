import pytest

from brownie import ZERO_ADDRESS
from tests.conftest import approx

REWARD = 10 ** 20
WEEK = 7 * 86400


@pytest.fixture(scope="module", autouse=True)
def initial_setup(
    alice, chain, coin_reward, reward_contract, token, mock_lp_token, gauge_v2, gauge_controller, minter
):
    # gauge setup
    token.set_minter(minter, {'from': alice})
    gauge_controller.add_type(b'Liquidity', 10**10, {'from': alice})
    gauge_controller.add_gauge(gauge_v2, 0, 0, {'from': alice})

    # deposit into gauge
    mock_lp_token.approve(gauge_v2, 2**256-1, {'from': alice})
    gauge_v2.deposit(10**18, {'from': alice})

    # add rewards
    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:]
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{sigs[2]}{'00' * 20}"

    gauge_v2.set_rewards(
        reward_contract,
        sigs,
        [coin_reward] + [ZERO_ADDRESS] * 7,
        {'from': alice}
    )

    # fund rewards
    coin_reward._mint_for_testing(REWARD, {'from': reward_contract})
    reward_contract.notifyRewardAmount(REWARD, {'from': alice})

    # sleep half way through the reward period
    chain.sleep(int(86400 * 3.5))


def test_transfer_triggers_claim_for_sender(alice, bob, chain, gauge_v2, coin_reward):
    amount = gauge_v2.balanceOf(alice)

    gauge_v2.transfer(bob, amount, {'from': alice})

    reward = coin_reward.balanceOf(alice)
    assert approx(REWARD // 2, reward, 1e-4)


def test_transfer_triggers_claim_for_receiver(alice, bob, chain, gauge_v2, coin_reward):
    amount = gauge_v2.balanceOf(alice) // 2

    gauge_v2.transfer(bob, amount, {'from': alice})
    chain.sleep(WEEK)
    gauge_v2.transfer(alice, amount, {'from': bob})

    rewards = []
    for acct in (alice, bob):
        gauge_v2.claim_rewards({'from': acct})
        rewards += [coin_reward.balanceOf(acct)]

    assert sum(rewards) <= REWARD
    assert approx(rewards[0] / rewards[1], 3, 1e-4)
    assert approx(REWARD, sum(rewards), 1.001 / WEEK)


def test_transfer_partial_balance(alice, bob, chain, gauge_v2, coin_reward):
    amount = gauge_v2.balanceOf(alice) // 2

    gauge_v2.transfer(bob, amount, {'from': alice})
    chain.sleep(WEEK)

    rewards = []
    for acct in (alice, bob):
        gauge_v2.claim_rewards({'from': acct})
        rewards += [coin_reward.balanceOf(acct)]

    assert sum(rewards) <= REWARD
    assert approx(rewards[0] / rewards[1], 3, 1e-4)
    assert approx(REWARD, sum(rewards), 1.001 / WEEK)


def test_transfer_full_balance(alice, bob, chain, gauge_v2, coin_reward):
    amount = gauge_v2.balanceOf(alice)

    gauge_v2.transfer(bob, amount, {'from': alice})
    chain.sleep(WEEK)

    rewards = []
    for acct in (alice, bob):
        gauge_v2.claim_rewards({'from': acct})
        rewards += [coin_reward.balanceOf(acct)]

    assert sum(rewards) <= REWARD
    assert approx(rewards[0], rewards[1], 1e-4)
    assert approx(REWARD, sum(rewards), 1.001 / WEEK)


def test_transfer_zero_tokens(alice, bob, chain, gauge_v2, coin_reward):
    gauge_v2.transfer(bob, 0, {'from': alice})
    chain.sleep(WEEK)

    for acct in (alice, bob):
        gauge_v2.claim_rewards({'from': acct})

    reward = coin_reward.balanceOf(alice)

    assert coin_reward.balanceOf(bob) == 0
    assert reward <= REWARD
    assert approx(REWARD, reward, 1.001 / WEEK)


def test_transfer_to_self(alice, chain, gauge_v2, coin_reward):
    sender_balance = gauge_v2.balanceOf(alice)
    amount = sender_balance // 4

    gauge_v2.transfer(alice, amount, {'from': alice})
    chain.sleep(WEEK)

    gauge_v2.claim_rewards({'from': alice})
    reward = coin_reward.balanceOf(alice)

    assert reward <= REWARD
    assert approx(REWARD, reward, 1.001 / WEEK)
