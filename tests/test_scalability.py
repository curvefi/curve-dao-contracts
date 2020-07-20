import brownie
from brownie import chain
from brownie.test import strategy

GAUGE_COUNT = 100
TYPE_COUNT = 3
USER_COUNT = 5


class StateMachine:
    """
    Long-running stateful test to validate that gas costs are not prohibitively high
    when using many liquidity gauges.

    Strategies
    ----------
    st_account : address
        Account to send transaction from
    st_amount : int
        Deposit amount
    st_gauge : int
        Index value used to choose a liquidity gauge contract
    st_weight : int
        Vote weight
    """

    st_account = strategy("address", length=USER_COUNT)
    st_amount = strategy("uint", min_value=10**17, max_value=10**19)
    st_gauge = strategy("uint", max_value=GAUGE_COUNT-1)
    st_weight = strategy("uint", max_value=10000)

    def __init__(self, accounts, gauge_controller, gauges, mock_lp_token, minter):
        self.gauges = gauges
        self.accounts = accounts

        self.lp_token = mock_lp_token
        self.minter = minter
        self.controller = gauge_controller

    def setup(self):
        self.last_voted = {i: [0]*GAUGE_COUNT for i in self.accounts}
        self.vote_weights = {i: [0]*GAUGE_COUNT for i in self.accounts}
        self.balances = {i: [0]*GAUGE_COUNT for i in self.accounts}

    def rule_vote(self, st_account, st_gauge, st_weight):
        # check that this account has not voted recently
        if chain.time() - self.last_voted[st_account][st_gauge] < 86400*10:
            with brownie.reverts("Cannot vote so often"):
                self.controller.vote_for_gauge_weights(
                    self.gauges[st_gauge], st_weight, {'from': st_account}
                )
            return

        # check that this account has not used all it's voting power
        votes = self.vote_weights[st_account].copy()
        votes[st_gauge] = st_weight
        if sum(votes) > 10000:
            with brownie.reverts():
                self.controller.vote_for_gauge_weights(
                    self.gauges[st_gauge], st_weight, {'from': st_account}
                )
            return

        # place a vote and adjust vote weights
        self.controller.vote_for_gauge_weights(
            self.gauges[st_gauge], st_weight, {'from': st_account}
        )
        self.vote_weights[st_account][st_gauge] = st_weight
        self.last_voted[st_account][st_gauge] = chain[-1].timestamp

    def rule_deposit(self, st_account, st_gauge, st_amount):
        # `st_account` deposits `st_amount` into `gauges[st_gauge]`
        self.balances[st_account][st_gauge] += st_amount
        gauge = self.gauges[st_gauge]
        self.lp_token.approve(gauge, st_amount, {'from': st_account})
        gauge.deposit(st_amount, {'from': st_account})

    def rule_withdraw(self, st_account):
        # `st_account` withdraws their full balance from a single gauge
        # if no balance has been deposited, withdraw 0 tokens from `gauges[0]`
        idx = next((i for i in range(GAUGE_COUNT) if self.balances[st_account][i]), 0)
        gauge = self.gauges[idx]
        gauge.withdraw(self.balances[st_account][idx], {'from': st_account})
        self.balances[st_account][idx] = 0

    def rule_mint(self, st_account):
        # `st_account` mints from a single gauge
        idx = next((i for i in range(GAUGE_COUNT) if self.balances[st_account][i]), 0)
        self.minter.mint(self.gauges[idx], {'from': st_account})

    def invariant_advance_time(self):
        # advance the clock by one week between each action
        chain.sleep(86400 * 7)


def test_scalability(
    state_machine,
    LiquidityGauge,
    accounts,
    gauge_controller,
    mock_lp_token,
    minter,
    token,
    voting_escrow
):
    token.set_minter(minter, {'from': accounts[0]})

    for i in range(USER_COUNT):
        mock_lp_token.transfer(accounts[i], 10**22, {'from': accounts[0]})
        token.transfer(accounts[i], 10**22, {'from': accounts[0]})
        token.approve(voting_escrow, 10**22, {'from': accounts[i]})
        voting_escrow.create_lock(10**22, chain.time() + 86400 * 365 * 2, {'from': accounts[i]})

    for i in range(TYPE_COUNT):
        gauge_controller.add_type(i, 10**18, {'from': accounts[0]})

    gauges = []
    for i in range(GAUGE_COUNT):
        contract = LiquidityGauge.deploy(mock_lp_token, minter, {'from': accounts[0]})
        gauge_controller.add_gauge(contract, i % TYPE_COUNT, {'from': accounts[0]})
        gauges.append(contract)

    state_machine(
        StateMachine,
        accounts[:USER_COUNT],
        gauge_controller,
        gauges,
        mock_lp_token,
        minter,
        settings={'max_examples': 50, 'stateful_step_count': 100}
    )
