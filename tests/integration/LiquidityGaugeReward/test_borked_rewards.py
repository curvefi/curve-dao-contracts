import pytest
from brownie.test import given, strategy
from hypothesis import settings

@pytest.fixture(scope="module", autouse=True)
def initial_setup(accounts, reward_contract, mock_lp_token, liquidity_gauge_reward):
    mock_lp_token.approve(liquidity_gauge_reward, 2 ** 256-1, {'from': accounts[0]})
    liquidity_gauge_reward.deposit(100000, {'from': accounts[0]})

    for i in range(1, 11):
        mock_lp_token.transfer(accounts[i], 10**18, {'from': accounts[0]})
        mock_lp_token.approve(liquidity_gauge_reward, 10**18, {'from': accounts[i]})


@given(
    amounts=strategy("uint256[10]", min_value=10**17, max_value=10**18, unique=True),
    durations=strategy("uint256[10]", max_value=86400*30, unique=True),
)
@settings(max_examples=10)
def test_withdraw_borked_rewards(
    accounts, chain, reward_contract, mock_lp_token, liquidity_gauge_reward, amounts, durations
):
    for i, (amount, duration) in enumerate(zip(amounts, durations), start=1):
        liquidity_gauge_reward.deposit(amount, {'from': accounts[i]})
        chain.sleep(duration)

    # Calling this method without transfering tokens breaks `CurveRewards.getReward`
    # however, it should still be possible to withdraw if `claim_rewards = False`
    reward_contract.notifyRewardAmount(10 ** 20, {'from': accounts[0]})

    for i, (amount, duration) in enumerate(zip(amounts, durations), start=1):
        liquidity_gauge_reward.withdraw(amount, False, {'from': accounts[i]})
        assert mock_lp_token.balanceOf(accounts[i]) == 10**18
