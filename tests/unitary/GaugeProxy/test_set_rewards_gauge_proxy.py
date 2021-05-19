import brownie
import pytest
from brownie import ZERO_ADDRESS


@pytest.fixture(scope="module", autouse=True)
def setup(alice, gauge_proxy, gauge_v2, mock_lp_token):
    gauge_v2.commit_transfer_ownership(gauge_proxy, {"from": alice})
    gauge_proxy.accept_transfer_ownership(gauge_v2, {"from": alice})
    mock_lp_token.approve(gauge_v2, 10 ** 18, {"from": alice})
    gauge_v2.deposit(10 ** 18, {"from": alice})


def test_set_rewards(alice, gauge_proxy, gauge_v2, reward_contract, coin_reward):
    sigs = [
        reward_contract.stake.signature[2:],
        reward_contract.withdraw.signature[2:],
        reward_contract.getReward.signature[2:],
    ]
    sigs = f"0x{sigs[0]}{sigs[1]}{sigs[2]}{'00' * 20}"

    gauge_proxy.set_rewards(
        gauge_v2, reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice},
    )
    assert gauge_v2.reward_contract() == reward_contract
    assert gauge_v2.reward_tokens(0) == coin_reward


@pytest.mark.parametrize("idx", [1, 2])
def test_only_ownership_admin(accounts, gauge_proxy, gauge_v2, reward_contract, idx):

    with brownie.reverts("Access denied"):
        gauge_proxy.set_rewards(
            gauge_v2, reward_contract, "0x00", [ZERO_ADDRESS] * 8, {"from": accounts[idx]},
        )
