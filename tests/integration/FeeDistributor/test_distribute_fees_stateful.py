from brownie import chain
from brownie.test import strategy

WEEK = 86400 * 7
YEAR = 86400 * 365


class StateMachine:

    st_acct = strategy('address', length=5)
    st_weeks = strategy('uint256', min_value=1, max_value=12)
    st_amount = strategy('decimal', min_value=1, max_value=100, places=3)

    def __init__(cls, distributor, accounts, voting_escrow, fee_coin):
        cls.distributor = distributor
        cls.accounts = accounts
        cls.voting_escrow = voting_escrow
        cls.fee_coin = fee_coin

    def setup(self):
        self.locked_until = {self.accounts[0]: self.voting_escrow.locked__end(self.accounts[0])}

    def _check_active_lock(self, st_acct):
        # check if `st_acct` has an active lock
        if st_acct not in self.locked_until:
            return False

        if self.locked_until[st_acct] < chain.time():
            self.voting_escrow.withdraw({'from': st_acct})
            del self.locked_until[st_acct]
            return False

        return True

    def initialize_new_lock(self, st_acct, st_amount, st_weeks):
        """
        Initialize-only rule to make a new lock.

        This is equivalent to `rule_new_lock` to make it more likely we have at
        least 2 accounts locked at the start of the test run.
        """
        self.rule_new_lock(st_acct, st_amount, st_weeks)

    def rule_new_lock(self, st_acct, st_amount, st_weeks):
        """
        Add a new user lock.

        Arguments
        ---------
        st_acct : Account
            Account to lock tokens for. If this account already has an active
            lock, the rule is skipped.
        st_amount : decimal
            Amount of tokens to lock.
        st_weeks : int
            Duration of lock, given in weeks.
        """
        if not self._check_active_lock(st_acct):
            until = ((chain.time() // WEEK) + st_weeks) * WEEK
            self.voting_escrow.create_lock(int(st_amount * 10**18), until, {'from': st_acct})
            self.locked_until[st_acct] = until

    def rule_extend_lock(self, st_acct, st_weeks):
        """
        Extend an existing user lock.

        Arguments
        ---------
        st_acct : Account
            Account to extend lock for. If this account does not have an active
            lock, the rule is skipped.
        st_weeks : int
            Duration to extend the lock, given in weeks.
        """
        if self._check_active_lock(st_acct):
            until = ((self.locked_until[st_acct] // WEEK) + st_weeks) * WEEK
            until = min(until, (chain.time() + YEAR * 4) // WEEK * WEEK)

            self.voting_escrow.increase_unlock_time(until, {'from': st_acct})
            self.locked_until[st_acct] = until

    def rule_increase_lock_amount(self, st_acct, st_amount):
        """
        Increase the amount of an existing user lock.

        Arguments
        ---------
        st_acct : Account
            Account to increase lock amount for. If this account does not have an
            active lock, the rule is skipped.
        st_amount : decimal
            Amount of tokens to add to lock.
        """
        if self._check_active_lock(st_acct):
            self.voting_escrow.increase_amount(int(st_amount * 10**18), {'from': st_acct})

    def rule_claim_fees(self, st_acct):
        """
        Claim fees for a user.

        Arguments
        ---------
        st_acct : Account
            Account to claim fees for.
        """
        self.distributor.claim({'from': st_acct})

    def rule_increase_available_fees(self, st_amount):
        """
        Transfer additional fees into the distributor and make a checkpoint.

        Arguments
        ---------
        st_amount : decimal
            Amount of fee tokens to add to the distributor.
        """
        self.fee_coin._mint_for_testing(int(st_amount * 10**18), {'from': self.distributor.address})
        self.distributor.checkpoint_token()

    def invariant_advance_time(self):
        """
        Advance time by one week and checkpoint the total supply.
        """
        chain.sleep(WEEK)
        self.distributor.checkpoint_total_supply()

    def teardown(self):
        """
        Claim fees for all accounts and verify that only dust remains.
        """
        chain.sleep(WEEK)
        for acct in self.accounts:
            self.distributor.claim({'from': acct})

        assert self.fee_coin.balanceOf(self.distributor) < 100


def test_stateful(state_machine, accounts, voting_escrow, fee_distributor, coin_a, token):
    for i in range(5):
        # ensure accounts[:5] all have tokens that may be locked
        token.approve(voting_escrow, 2**256-1, {'from': accounts[i]})
        token.transfer(accounts[i], 10**18 * 10000000, {'from': accounts[0]})

    # accounts[0] locks 10000000 tokens for 2 years - longer than the maximum duration of the test
    voting_escrow.create_lock(10**18 * 10000000, chain.time() + YEAR * 2, {'from': accounts[0]})

    # a week later we deploy the fee distributor and make an initial deposit
    chain.sleep(WEEK)
    distributor = fee_distributor()
    distributor.toggle_allow_checkpoint_token()
    coin_a._mint_for_testing(10**18, {'from': distributor.address})
    distributor.checkpoint_token()

    state_machine(
        StateMachine,
        distributor,
        accounts[:5],
        voting_escrow,
        coin_a,
        settings={'stateful_step_count': 30}
    )
