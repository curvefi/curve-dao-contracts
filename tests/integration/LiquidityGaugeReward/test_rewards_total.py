import brownie
from brownie import chain
from brownie.test import strategy
from tests.conftest import approx


class StateMachine:
    """
    Validate that eventually users claim almost all rewards (except for dust)
    """

    st_account = strategy("address", length=5)
    st_value = strategy("uint64", min_value=10 ** 10)
    st_time = strategy("uint", max_value=365 * 86400)
    st_reward = strategy("uint64")

    def __init__(self, accounts, liquidity_gauge_reward, mock_lp_token,
                 reward_contract, coin_reward):
        self.accounts = accounts
        self.token = mock_lp_token
        self.liquidity_gauge = liquidity_gauge_reward
        self.coin_reward = coin_reward
        self.reward_contract = reward_contract

    def setup(self):
        self.balances = {i: 0 for i in self.accounts}
        self.rewards_total = 0
        self.total_balances = 0

    def rule_deposit(self, st_account, st_value):
        """
        Make a deposit into the `LiquidityGauge` contract.

        Because of the upper bound of `st_value` relative to the initial account
        balances, this rule should never fail.
        """
        balance = self.token.balanceOf(st_account)

        self.liquidity_gauge.deposit(st_value, {"from": st_account})
        self.balances[st_account] += st_value
        self.total_balances += st_value

        assert self.token.balanceOf(st_account) == balance - st_value

    def rule_notify_reward(self, st_reward):
        """
        Add rewards only if at least someone has deposits
        """
        if self.total_balances > 0:
            self.coin_reward._mint_for_testing(st_reward)
            self.coin_reward.transfer(self.reward_contract, st_reward)
            self.reward_contract.notifyRewardAmount(st_reward)
            self.rewards_total += st_reward

    def rule_withdraw(self, st_account, st_value):
        """
        Attempt to withdraw from the `LiquidityGauge` contract.
        Don't withdraw if this leads to empty contract (rewards won't go to anyone)
        """
        if st_value >= self.total_balances:
            return

        if self.balances[st_account] < st_value:
            # fail path - insufficient balance
            with brownie.reverts():
                self.liquidity_gauge.withdraw(st_value, {"from": st_account})
            return

        # success path
        balance = self.token.balanceOf(st_account)
        self.liquidity_gauge.withdraw(st_value, {"from": st_account})
        self.balances[st_account] -= st_value
        self.total_balances -= st_value

        assert self.token.balanceOf(st_account) == balance + st_value

    def rule_claim(self, st_account):
        self.liquidity_gauge.claim_rewards({'from': st_account})

    def rule_advance_time(self, st_time):
        """
        Advance the clock.
        """
        chain.sleep(st_time)

    def rule_checkpoint(self, st_account):
        """
        Create a new user checkpoint.
        """
        self.liquidity_gauge.user_checkpoint(st_account, {"from": st_account})

    def invariant_balances(self):
        """
        Validate expected balances against actual balances.
        """
        for account, balance in self.balances.items():
            assert self.liquidity_gauge.balanceOf(account) == balance

    def invariant_total_supply(self):
        """
        Validate expected total supply against actual total supply.
        """
        assert self.liquidity_gauge.totalSupply() == sum(self.balances.values())

    def teardown(self):
        """
        Travel far enough in future for all rewards to be distributed (1 week)
        and claim all
        """
        chain.sleep(2 * 7 * 86400)
        rewards_claimed = 0
        for act in self.accounts:
            self.liquidity_gauge.claim_rewards({'from': act})
            rewards_claimed += self.coin_reward.balanceOf(act)

        if self.rewards_total > 7 * 86400:  # Otherwise we may have 0 claimed
            precision = max(7 * 86400 / self.rewards_total * 2, 1e-10)
            assert approx(rewards_claimed, self.rewards_total, precision)


def test_state_machine(
        state_machine, accounts, liquidity_gauge_reward, mock_lp_token,
        reward_contract, coin_reward, no_call_coverage):
    # fund accounts to be used in the test
    for acct in accounts[1:5]:
        mock_lp_token.transfer(acct, 10 ** 21, {"from": accounts[0]})

    # approve liquidity_gauge from the funded accounts
    for acct in accounts[:5]:
        mock_lp_token.approve(liquidity_gauge_reward, 2 ** 256 - 1, {"from": acct})

    # because this is a simple state machine, we use more steps than normal
    settings = {"stateful_step_count": 25}

    state_machine(StateMachine, accounts, liquidity_gauge_reward, mock_lp_token, reward_contract, coin_reward, settings=settings)
