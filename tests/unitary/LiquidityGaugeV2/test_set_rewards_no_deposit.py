import brownie
import pytest
from brownie import ZERO_ADDRESS

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
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract.getReward.signature[2:]}{'00' * 20}"
    gauge_v2.set_rewards(reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})


def test_unset_no_totalsupply(alice, coin_reward, reward_contract, gauge_v2, mock_lp_token):
    gauge_v2.set_rewards(ZERO_ADDRESS, "0x00", [ZERO_ADDRESS] * 8, {"from": alice})

    assert mock_lp_token.allowance(gauge_v2, reward_contract) == 0
    assert gauge_v2.reward_contract() == ZERO_ADDRESS
    assert [gauge_v2.reward_tokens(i) for i in range(8)] == [ZERO_ADDRESS] * 8


def test_unset_with_totalsupply(alice, coin_reward, reward_contract, gauge_v2, mock_lp_token):
    gauge_v2.deposit(LP_AMOUNT, {"from": alice})
    gauge_v2.set_rewards(ZERO_ADDRESS, "0x00", [ZERO_ADDRESS] * 8, {"from": alice})

    assert mock_lp_token.allowance(gauge_v2, reward_contract) == 0
    assert mock_lp_token.balanceOf(gauge_v2) == LP_AMOUNT
    assert gauge_v2.reward_contract() == ZERO_ADDRESS
    assert [gauge_v2.reward_tokens(i) for i in range(8)] == [ZERO_ADDRESS] * 8


def test_modify_no_deposit_no_ts(reward_contract_2, alice, gauge_v2, coin_a, mock_lp_token):
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract_2.getReward.signature[2:]}{'00' * 20}"
    gauge_v2.set_rewards(reward_contract_2, sigs, [coin_a] + [ZERO_ADDRESS] * 7, {"from": alice})

    assert gauge_v2.reward_contract() == reward_contract_2
    assert gauge_v2.reward_tokens(0) == coin_a
    assert gauge_v2.reward_tokens(1) == ZERO_ADDRESS


def test_modify_no_deposit(
    reward_contract, reward_contract_2, alice, gauge_v2, chain, coin_a, coin_reward, mock_lp_token,
):
    gauge_v2.deposit(LP_AMOUNT, {"from": alice})
    coin_reward._mint_for_testing(REWARD, {"from": reward_contract})
    reward_contract.notifyRewardAmount(REWARD, {"from": alice})
    chain.sleep(86400)

    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract_2.getReward.signature[2:]}{'00' * 20}"
    gauge_v2.set_rewards(reward_contract_2, sigs, [coin_a] + [ZERO_ADDRESS] * 7, {"from": alice})

    assert mock_lp_token.balanceOf(gauge_v2) == LP_AMOUNT
    assert gauge_v2.reward_contract() == reward_contract_2
    assert gauge_v2.reward_tokens(0) == coin_a
    assert gauge_v2.reward_tokens(1) == ZERO_ADDRESS


def test_modify_deposit(
    reward_contract, reward_contract_2, alice, gauge_v2, chain, coin_a, coin_reward, mock_lp_token,
):
    gauge_v2.deposit(LP_AMOUNT, {"from": alice})
    coin_reward._mint_for_testing(REWARD, {"from": reward_contract})
    reward_contract.notifyRewardAmount(REWARD, {"from": alice})
    chain.sleep(86400)

    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{sigs[2]}{'00' * 20}"
    gauge_v2.set_rewards(reward_contract_2, sigs, [coin_a] + [ZERO_ADDRESS] * 7, {"from": alice})

    assert mock_lp_token.balanceOf(reward_contract_2) == LP_AMOUNT
    assert gauge_v2.reward_contract() == reward_contract_2
    assert gauge_v2.reward_tokens(0) == coin_a
    assert gauge_v2.reward_tokens(1) == ZERO_ADDRESS


def test_modify_deposit_no_ts(reward_contract_2, alice, gauge_v2, coin_a):
    sigs = [
        reward_contract_2.stake.signature[2:],
        reward_contract_2.withdraw.signature[2:],
        reward_contract_2.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{sigs[2]}{'00' * 20}"
    with brownie.reverts("dev: zero total supply"):
        gauge_v2.set_rewards(
            reward_contract_2, sigs, [coin_a] + [ZERO_ADDRESS] * 7, {"from": alice}
        )
