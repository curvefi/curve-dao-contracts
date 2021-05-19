import pytest
from brownie import ZERO_ADDRESS

from tests.conftest import approx

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


@pytest.fixture(scope="module")
def reward_contract_2(CurveRewards, mock_lp_token, accounts, coin_a):
    contract = CurveRewards.deploy(mock_lp_token, coin_a, {"from": accounts[0]})
    contract.setRewardDistribution(accounts[0], {"from": accounts[0]})
    yield contract


@pytest.fixture(scope="module", autouse=True)
def initial_setup(gauge_v2, mock_lp_token, alice, reward_contract, coin_reward):
    mock_lp_token.approve(gauge_v2, LP_AMOUNT, {"from": alice})
    gauge_v2.deposit(LP_AMOUNT, {"from": alice})

    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{sigs[2]}{'00' * 20}"
    gauge_v2.set_rewards(reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})

    coin_reward._mint_for_testing(REWARD, {"from": reward_contract})
    reward_contract.notifyRewardAmount(REWARD, {"from": alice})


def test_unset_and_claim_historic(alice, chain, coin_reward, reward_contract, gauge_v2):
    chain.sleep(WEEK)
    gauge_v2.set_rewards(ZERO_ADDRESS, "0x00", [ZERO_ADDRESS] * 8, {"from": alice})

    gauge_v2.claim_historic_rewards([coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})

    reward = coin_reward.balanceOf(alice)
    assert reward <= REWARD
    assert approx(REWARD, reward, 1.001 / WEEK)


def test_claim_historic_multiple(
    alice, chain, coin_reward, coin_a, reward_contract, reward_contract_2, gauge_v2
):
    chain.sleep(WEEK)

    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{sigs[2]}{'00' * 20}"
    gauge_v2.set_rewards(reward_contract_2, sigs, [coin_a] + [ZERO_ADDRESS] * 7, {"from": alice})

    coin_a._mint_for_testing(REWARD, {"from": reward_contract_2})
    reward_contract_2.notifyRewardAmount(REWARD, {"from": alice})

    chain.sleep(WEEK)
    gauge_v2.set_rewards(ZERO_ADDRESS, "0x00", [ZERO_ADDRESS] * 8, {"from": alice})

    gauge_v2.claim_historic_rewards([coin_reward, coin_a] + [ZERO_ADDRESS] * 6, {"from": alice})

    for coin in (coin_reward, coin_a):
        reward = coin.balanceOf(alice)
        assert reward <= REWARD
        assert approx(REWARD, reward, 1.001 / WEEK)


def test_claim_historic_while_active(alice, bob, chain, gauge_v2, coin_reward):
    amount = gauge_v2.balanceOf(alice) // 2

    chain.sleep(int(86400 * 3.5))
    gauge_v2.transfer(bob, amount, {"from": alice})
    chain.sleep(WEEK)

    # this should have no effect
    gauge_v2.claim_historic_rewards([coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})
    gauge_v2.claim_historic_rewards([coin_reward] + [ZERO_ADDRESS] * 7, {"from": bob})

    assert approx(coin_reward.balanceOf(alice) / REWARD, 0.5, 1e-4)
    assert coin_reward.balanceOf(bob) == 0

    # correctly claiming after `claim_historic_rewards` should still work as expected
    rewards = []
    for acct in (alice, bob):
        gauge_v2.claim_rewards({"from": acct})
        rewards += [coin_reward.balanceOf(acct)]

    assert sum(rewards) <= REWARD
    assert approx(rewards[0] / rewards[1], 3, 1e-4)
    assert approx(REWARD, sum(rewards), 1.001 / WEEK)


def test_repeat_token(alice, bob, chain, coin_reward, reward_contract, gauge_v2):
    amount = gauge_v2.balanceOf(alice) // 2

    chain.sleep(int(86400 * 3.5))
    gauge_v2.transfer(bob, amount, {"from": alice})
    chain.sleep(WEEK)

    gauge_v2.set_rewards(ZERO_ADDRESS, "0x00", [ZERO_ADDRESS] * 8, {"from": alice})

    # repeated use of the same coin in `claim_historic_rewards` should have no effect
    gauge_v2.claim_historic_rewards([coin_reward] * 8, {"from": bob})

    reward = coin_reward.balanceOf(bob)
    assert reward <= REWARD
    assert approx(reward / REWARD, 0.25, 1e-4)
