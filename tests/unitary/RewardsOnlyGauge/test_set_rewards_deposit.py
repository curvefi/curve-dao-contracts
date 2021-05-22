import brownie
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
def initial_setup(rewards_only_gauge, mock_lp_token, alice, reward_contract, coin_reward):
    mock_lp_token.approve(rewards_only_gauge, 2 ** 256 - 1, {"from": alice})
    rewards_only_gauge.deposit(1, {"from": alice})

    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{sigs[2]}{'00' * 20}"
    rewards_only_gauge.set_rewards(
        reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
    )

    rewards_only_gauge.withdraw(1, {"from": alice})


def test_unset_no_totalsupply(
    alice, coin_reward, reward_contract, rewards_only_gauge, mock_lp_token
):
    rewards_only_gauge.set_rewards(
        ZERO_ADDRESS, "0x00", [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
    )

    assert mock_lp_token.allowance(rewards_only_gauge, reward_contract) == 0
    assert rewards_only_gauge.reward_contract() == ZERO_ADDRESS
    assert [rewards_only_gauge.reward_tokens(i) for i in range(8)] == [coin_reward] + [
        ZERO_ADDRESS
    ] * 7


def test_unset_with_totalsupply(
    alice, coin_reward, reward_contract, rewards_only_gauge, mock_lp_token
):
    rewards_only_gauge.deposit(LP_AMOUNT, {"from": alice})
    rewards_only_gauge.set_rewards(
        ZERO_ADDRESS, "0x00", [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
    )

    assert mock_lp_token.allowance(rewards_only_gauge, reward_contract) == 0
    assert mock_lp_token.balanceOf(rewards_only_gauge) == LP_AMOUNT
    assert rewards_only_gauge.reward_contract() == ZERO_ADDRESS
    assert [rewards_only_gauge.reward_tokens(i) for i in range(8)] == [coin_reward] + [
        ZERO_ADDRESS
    ] * 7


def test_unsetting_claims(alice, chain, coin_reward, reward_contract, rewards_only_gauge):
    rewards_only_gauge.deposit(LP_AMOUNT, {"from": alice})

    coin_reward._mint_for_testing(REWARD, {"from": reward_contract})
    reward_contract.notifyRewardAmount(REWARD, {"from": alice})

    chain.sleep(WEEK)

    rewards_only_gauge.set_rewards(
        ZERO_ADDRESS, "0x00", [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
    )

    reward = coin_reward.balanceOf(rewards_only_gauge)
    assert reward <= REWARD
    assert approx(REWARD, reward, 1.001 / WEEK)


def test_modify_no_deposit_no_ts(reward_contract_2, alice, rewards_only_gauge, coin_a, coin_reward):
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract_2.getReward.signature[2:]}{'00' * 20}"
    rewards_only_gauge.set_rewards(
        reward_contract_2, sigs, [coin_reward, coin_a] + [ZERO_ADDRESS] * 6, {"from": alice}
    )

    assert rewards_only_gauge.reward_contract() == reward_contract_2
    assert [rewards_only_gauge.reward_tokens(i) for i in range(3)] == [
        coin_reward,
        coin_a,
        ZERO_ADDRESS,
    ]


def test_modify_no_deposit(
    reward_contract,
    reward_contract_2,
    alice,
    rewards_only_gauge,
    chain,
    coin_a,
    coin_reward,
    mock_lp_token,
):
    rewards_only_gauge.deposit(LP_AMOUNT, {"from": alice})
    coin_reward._mint_for_testing(REWARD, {"from": reward_contract})
    reward_contract.notifyRewardAmount(REWARD, {"from": alice})
    chain.sleep(86400)

    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract_2.getReward.signature[2:]}{'00' * 20}"
    rewards_only_gauge.set_rewards(
        reward_contract_2, sigs, [coin_reward, coin_a] + [ZERO_ADDRESS] * 6, {"from": alice}
    )

    assert mock_lp_token.balanceOf(rewards_only_gauge) == LP_AMOUNT
    assert rewards_only_gauge.reward_contract() == reward_contract_2
    assert [rewards_only_gauge.reward_tokens(i) for i in range(3)] == [
        coin_reward,
        coin_a,
        ZERO_ADDRESS,
    ]
    assert coin_reward.balanceOf(rewards_only_gauge) > 0


def test_modify_deposit(
    reward_contract,
    reward_contract_2,
    alice,
    rewards_only_gauge,
    chain,
    coin_a,
    coin_reward,
    mock_lp_token,
):
    rewards_only_gauge.deposit(LP_AMOUNT, {"from": alice})
    coin_reward._mint_for_testing(REWARD, {"from": reward_contract})
    reward_contract.notifyRewardAmount(REWARD, {"from": alice})
    chain.sleep(86400)

    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{sigs[2]}{'00' * 20}"
    rewards_only_gauge.set_rewards(
        reward_contract_2, sigs, [coin_reward, coin_a] + [ZERO_ADDRESS] * 6, {"from": alice}
    )

    assert mock_lp_token.balanceOf(reward_contract_2) == LP_AMOUNT
    assert rewards_only_gauge.reward_contract() == reward_contract_2
    assert [rewards_only_gauge.reward_tokens(i) for i in range(3)] == [
        coin_reward,
        coin_a,
        ZERO_ADDRESS,
    ]
    assert coin_reward.balanceOf(rewards_only_gauge) > 0


def test_modify_deposit_no_ts(reward_contract_2, alice, rewards_only_gauge, coin_a, coin_reward):
    sigs = [
        reward_contract_2.stake.signature[2:],
        reward_contract_2.withdraw.signature[2:],
        reward_contract_2.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{sigs[2]}{'00' * 20}"
    with brownie.reverts("dev: zero total supply"):
        rewards_only_gauge.set_rewards(
            reward_contract_2, sigs, [coin_reward, coin_a] + [ZERO_ADDRESS] * 6, {"from": alice}
        )
