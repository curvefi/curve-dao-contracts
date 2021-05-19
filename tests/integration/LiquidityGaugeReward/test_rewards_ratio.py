from brownie.test import given, strategy
from hypothesis import settings

from tests.conftest import approx


@given(values=strategy("uint[8]", min_value=1, max_value=10 ** 21))
@settings(max_examples=25)
def test_ratio_equality(
    chain, accounts, liquidity_gauge_reward, mock_lp_token, reward_contract, coin_reward, values,
):
    N_acc = len(values)

    # fund accounts to be used in the test
    for acct in accounts[1:N_acc]:
        mock_lp_token.transfer(acct, 10 ** 21, {"from": accounts[0]})

    # approve liquidity_gauge from the funded accounts
    for acct in accounts[:N_acc]:
        mock_lp_token.approve(liquidity_gauge_reward, 2 ** 256 - 1, {"from": acct})

    # Deposit
    for value, act in zip(values, accounts[:N_acc]):
        liquidity_gauge_reward.deposit(value, {"from": act})

    # Fund rewards
    coin_reward._mint_for_testing(10 ** 20)
    coin_reward.transfer(reward_contract, 10 ** 20)
    reward_contract.notifyRewardAmount(10 ** 20)

    chain.sleep(2 * 7 * 86400)

    # Claim and measure rewards
    rewards = []
    for act in accounts[:N_acc]:
        before = coin_reward.balanceOf(act)
        liquidity_gauge_reward.claim_rewards({"from": act})
        after = coin_reward.balanceOf(act)
        rewards.append(after - before)

    for v, r in zip(values, rewards):
        if r > 0 and v > 0:
            precision = max(1 / min(r, v), 1e-15)
            assert approx(v / sum(values), r / sum(rewards), precision)
