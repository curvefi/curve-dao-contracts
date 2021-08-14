import brownie
import pytest
from brownie import ZERO_ADDRESS

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


@pytest.fixture(scope="module", autouse=True)
def initial_setup(gauge_v3, mock_lp_token, alice):
    mock_lp_token.approve(gauge_v3, LP_AMOUNT, {"from": alice})
    gauge_v3.deposit(LP_AMOUNT, {"from": alice})


def test_set_rewards_with_deposit(alice, coin_reward, reward_contract, mock_lp_token, gauge_v3):
    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{sigs[2]}{'00' * 20}"

    gauge_v3.set_rewards(reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})

    assert mock_lp_token.balanceOf(reward_contract) == LP_AMOUNT
    assert gauge_v3.reward_contract() == reward_contract
    assert gauge_v3.reward_tokens(0) == coin_reward
    assert gauge_v3.reward_tokens(1) == ZERO_ADDRESS


def test_set_rewards_no_deposit(alice, coin_reward, reward_contract, mock_lp_token, gauge_v3):
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract.getReward.signature[2:]}{'00' * 20}"
    gauge_v3.set_rewards(reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})

    assert mock_lp_token.balanceOf(gauge_v3) == LP_AMOUNT
    assert gauge_v3.reward_contract() == reward_contract
    assert gauge_v3.reward_tokens(0) == coin_reward
    assert gauge_v3.reward_tokens(1) == ZERO_ADDRESS


def test_multiple_reward_tokens(alice, coin_reward, coin_a, coin_b, reward_contract, gauge_v3):
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract.getReward.signature[2:]}{'00' * 20}"
    reward_tokens = [coin_reward, coin_a, coin_b] + [ZERO_ADDRESS] * 5

    gauge_v3.set_rewards(reward_contract, sigs, reward_tokens, {"from": alice})

    assert reward_tokens == [gauge_v3.reward_tokens(i) for i in range(8)]


def test_modify_reward_tokens_less(alice, coin_reward, coin_a, coin_b, reward_contract, gauge_v3):
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract.getReward.signature[2:]}{'00' * 20}"
    gauge_v3.set_rewards(
        reward_contract, sigs, [coin_reward, coin_a, coin_b] + [ZERO_ADDRESS] * 5, {"from": alice}
    )

    reward_tokens = [coin_reward] + [ZERO_ADDRESS] * 7
    with brownie.reverts("dev: cannot modify existing reward token"):
        gauge_v3.set_rewards(reward_contract, sigs, reward_tokens, {"from": alice})


def test_modify_reward_tokens_different(
    alice, coin_reward, coin_a, coin_b, reward_contract, gauge_v3
):
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract.getReward.signature[2:]}{'00' * 20}"
    gauge_v3.set_rewards(
        reward_contract, sigs, [coin_reward, coin_a, coin_b] + [ZERO_ADDRESS] * 5, {"from": alice}
    )

    reward_tokens = [coin_reward, coin_b, coin_a] + [ZERO_ADDRESS] * 5
    with brownie.reverts("dev: cannot modify existing reward token"):
        gauge_v3.set_rewards(reward_contract, sigs, reward_tokens, {"from": alice})


def test_modify_reward_tokens_more(alice, coin_reward, coin_a, coin_b, reward_contract, gauge_v3):
    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract.getReward.signature[2:]}{'00' * 20}"
    gauge_v3.set_rewards(reward_contract, sigs, [coin_a] + [ZERO_ADDRESS] * 7, {"from": alice})

    reward_tokens = [coin_a, coin_reward, coin_b] + [ZERO_ADDRESS] * 5
    gauge_v3.set_rewards(reward_contract, sigs, reward_tokens, {"from": alice})

    assert reward_tokens == [gauge_v3.reward_tokens(i) for i in range(8)]


def test_not_a_contract(alice, coin_reward, gauge_v3):
    with brownie.reverts("dev: not a contract"):
        gauge_v3.set_rewards(alice, "0x00", [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice})


def test_deposit_no_withdraw(alice, coin_reward, reward_contract, gauge_v3):
    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{'00' * 4}{sigs[2]}{'00' * 20}"

    with brownie.reverts("dev: failed withdraw"):
        gauge_v3.set_rewards(
            reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
        )


def test_withdraw_no_deposit(alice, coin_reward, reward_contract, gauge_v3):
    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{'00' * 4}{sigs[1]}{sigs[2]}{'00' * 20}"

    with brownie.reverts("dev: withdraw without deposit"):
        gauge_v3.set_rewards(
            reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
        )


def test_bad_deposit_sig(alice, coin_reward, reward_contract, gauge_v3):
    sigs = [
        "12345678",
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{'00' * 4}{sigs[2]}{'00' * 20}"

    with brownie.reverts("dev: failed deposit"):
        gauge_v3.set_rewards(
            reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
        )


def test_bad_withdraw_sig(alice, coin_reward, reward_contract, gauge_v3):
    sigs = [
        reward_contract.stake.signature[2:],
        "12345678",
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{'00' * 4}{sigs[2]}{'00' * 20}"

    with brownie.reverts("dev: failed withdraw"):
        gauge_v3.set_rewards(
            reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
        )


def test_no_reward_token(alice, reward_contract, gauge_v3):
    with brownie.reverts("dev: no reward token"):
        gauge_v3.set_rewards(reward_contract, "0x00", [ZERO_ADDRESS] * 8, {"from": alice})


def test_bad_claim_sig(alice, coin_reward, reward_contract, gauge_v3):
    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{'00' * 4}{'00' * 20}"

    with brownie.reverts("dev: bad claim sig"):
        gauge_v3.set_rewards(
            reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
        )
