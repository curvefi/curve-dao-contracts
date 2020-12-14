import pytest
from brownie import ZERO_ADDRESS

from tests.conftest import approx

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


@pytest.fixture(scope="module", autouse=True)
def initial_setup(
    alice, bob, chain, coin_reward, reward_contract, token, mock_lp_token, gauge_v2, gauge_controller, minter
):
    # gauge setup
    token.set_minter(minter, {'from': alice})
    gauge_controller.add_type(b'Liquidity', 10**10, {'from': alice})
    gauge_controller.add_gauge(gauge_v2, 0, 0, {'from': alice})

    # deposit into gauge
    mock_lp_token.transfer(bob, LP_AMOUNT, {'from': alice})
    mock_lp_token.approve(gauge_v2, LP_AMOUNT, {'from': bob})
    gauge_v2.deposit(LP_AMOUNT, {'from': bob})

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


def test_claim_one_lp(bob, chain, gauge_v2, coin_reward):
    chain.sleep(WEEK)

    gauge_v2.withdraw(LP_AMOUNT, {'from': bob})
    gauge_v2.claim_rewards({'from': bob})

    reward = coin_reward.balanceOf(bob)
    assert reward <= REWARD
    assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other(bob, charlie, chain, gauge_v2, coin_reward):
    chain.sleep(WEEK)

    gauge_v2.withdraw(LP_AMOUNT, {'from': bob})
    gauge_v2.claim_rewards(bob, {'from': charlie})

    assert coin_reward.balanceOf(charlie) == 0

    reward = coin_reward.balanceOf(bob)
    assert reward <= REWARD
    assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other_no_reward(bob, charlie, chain, gauge_v2, coin_reward):
    chain.sleep(WEEK)
    gauge_v2.claim_rewards(charlie, {'from': bob})

    assert coin_reward.balanceOf(bob) == 0
    assert coin_reward.balanceOf(charlie) == 0


def test_claim_two_lp(alice, bob, chain, gauge_v2, mock_lp_token,
                      coin_reward, no_call_coverage):

    # Deposit
    mock_lp_token.approve(gauge_v2, LP_AMOUNT, {'from': alice})
    gauge_v2.deposit(LP_AMOUNT, {'from': alice})

    chain.sleep(WEEK)
    chain.mine()

    # Calculate rewards
    claimable_rewards = [gauge_v2.claimable_reward.call(acc, coin_reward, {'from': acc})
                         for acc in (alice, bob)]

    # Claim rewards
    rewards = []
    for acct in (alice, bob):
        gauge_v2.claim_rewards({'from': acct})
        rewards += [coin_reward.balanceOf(acct)]

    # Calculation == results
    assert tuple(claimable_rewards) == tuple(rewards)

    # Approximately equal apart from what caused by 1 s ganache-cli jitter
    assert sum(rewards) <= REWARD
    assert approx(sum(rewards), REWARD, 1.001 / WEEK)  # ganache-cli jitter of 1 s
    assert approx(rewards[0], rewards[1], 2.002 * WEEK)
