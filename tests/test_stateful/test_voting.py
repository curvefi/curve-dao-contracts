import brownie
from brownie import history, rpc
from brownie.test import strategy

WEEK = 86400 * 7
MAX_TIME = 86400 * 365 * 4


class StateMachine:

    st_value = strategy('uint64')
    st_lock_duration = strategy('uint8')
    st_sleep_duration = strategy('uint', min_value=1, max_value=4)
    st_account = strategy('address')

    def __init__(self, accounts, token, voting_escrow):
        self.accounts = accounts
        self.token = token
        self.voting_escrow = voting_escrow

        for acct in accounts:
            token._mint_for_testing(10**40, {'from': acct})
            token.approve(voting_escrow, 2**256-1, {'from': acct})

    def setup(self):
        self.token_balances = {i: 10**40 for i in self.accounts}
        self.voting_balances = {i: {'value': 0, 'unlock_time': 0} for i in self.accounts}


    def rule_new_deposit(self, st_account, st_value, st_lock_duration):
        unlock_time = (rpc.time() + st_lock_duration * WEEK) // WEEK * WEEK

        if 0 < self.voting_balances[st_account]['unlock_time'] < rpc.time():
            # fail path - tokens are deposited, current lock has expired
            with brownie.reverts("Withdraw old tokens first"):
                self.voting_escrow.deposit(st_value, unlock_time, {'from': st_account})

        elif self.voting_balances[st_account]['unlock_time'] > unlock_time:
            # fail path - tokens are deposited, current lock is >= new lock
            with brownie.reverts("Cannot decrease the lock duration"):
                self.voting_escrow.deposit(st_value, unlock_time, {'from': st_account})

        elif st_value == 0:
            # fail path - tokens deposited, not advancing lock time or adding balance
            with brownie.reverts():
                self.voting_escrow.deposit(st_value, unlock_time, {'from': st_account})

        elif self.voting_balances[st_account]['value'] == 0 and unlock_time < rpc.time():
            # fail path - no deposit, unlock time is < current time
            with brownie.reverts("Can only lock until time in the future"):
                self.voting_escrow.deposit(st_value, unlock_time, {'from': st_account})

        elif unlock_time > rpc.time() + 86400 * 365 * 4:
            # fail path - no deposit, unlock time > four years later
            with brownie.reverts("Voting lock can be 4 years max"):
                self.voting_escrow.deposit(st_value, unlock_time, {'from': st_account})

        elif self.voting_balances[st_account]['value'] == 0 and st_value > 0:
            # success path - no tokens currently deposited
            tx = self.voting_escrow.deposit(st_value, unlock_time, {'from': st_account})
            self.voting_balances[st_account] = {
                'value': st_value,
                'unlock_time': tx.events['Deposit']['locktime'],
            }

        elif self.voting_balances[st_account]['unlock_time'] < unlock_time:
            # success path - tokens are deposited, current lock is < new lock
            tx = self.voting_escrow.deposit(st_value, unlock_time, {'from': st_account})
            self.voting_balances[st_account]['value'] += st_value
            self.voting_balances[st_account]['unlock_time'] = tx.events['Deposit']['locktime']


    def rule_increase_deposit_or_locktime(self, st_account, st_value):
        if self.voting_balances[st_account]['value'] == 0:
            # fail path - no tokens currently deposited
            with brownie.reverts("No existing lock found"):
                self.voting_escrow.deposit(st_value, {'from': st_account})

        elif self.voting_balances[st_account]['unlock_time'] < rpc.time():
            # fail path - tokens are deposited, current lock has expired
            with brownie.reverts("Cannot add to expired lock. Withdraw"):
                self.voting_escrow.deposit(st_value, {'from': st_account})

        elif st_value == 0:
            # fail path - tokens are deposited, value is zero
            with brownie.reverts():
                self.voting_escrow.deposit(st_value, {'from': st_account})

        else:
            # success path - tokens are deposited, lock has not expired
            self.voting_escrow.deposit(st_value, {'from': st_account})
            self.voting_balances[st_account]['value'] += st_value

    def rule_withdraw(self, st_account, st_value):
        if self.voting_balances[st_account]['unlock_time'] > rpc.time():
            # fail path - before unlock time
            with brownie.reverts("The lock didn't expire"):
                self.voting_escrow.withdraw(st_value, {'from': st_account})

        elif self.voting_balances[st_account]['value'] < st_value:
            # fail path - withdraw amount exceeds locked amount
            with brownie.reverts("Withdrawing more than you have"):
                self.voting_escrow.withdraw(st_value, {'from': st_account})

        elif st_value == 0:
            # success path - zero amount equals full amount
            self.voting_escrow.withdraw(st_value, {'from': st_account})
            self.voting_balances[st_account] = {'value': 0, 'unlock_time': 0}

        else:
            # success path - specific amount
            self.voting_escrow.withdraw(st_value, {'from': st_account})
            self.voting_balances[st_account]['value'] -= st_value

    def rule_advance_time(self, st_sleep_duration):
        rpc.sleep(st_sleep_duration * WEEK)
        self.token.balanceOf.transact(self.accounts[0], {'from': self.accounts[0]})

    def invariant_token_balances(self):
        for acct in self.accounts:
            assert self.token.balanceOf(acct) == 10**40 - self.voting_balances[acct]['value']

    def invariant_escrow_current_balances(self):
        total_supply = 0
        timestamp = history[-1].timestamp

        for acct in self.accounts:
            data = self.voting_balances[acct]

            balance = self.voting_escrow.balanceOf(acct)
            total_supply += balance

            if data['value'] * data['unlock_time'] > MAX_TIME * 1.1:
                assert balance
            elif not data['value'] or data['unlock_time'] < timestamp:
                assert not balance

        assert self.voting_escrow.totalSupply() == total_supply

    def invariant_historic_balances(self):
        total_supply = 0
        block_number = history[-4].block_number

        for acct in self.accounts:
            total_supply += self.voting_escrow.balanceOfAt(acct, block_number)

        assert self.voting_escrow.totalSupplyAt(block_number) == total_supply



def test_state_machine(state_machine, accounts, ERC20, VotingEscrow):
    token = ERC20.deploy("", "", 18, {'from': accounts[0]})
    voting_escrow = VotingEscrow.deploy(token, 'Voting-escrowed CRV', 'veCRV', 'veCRV_0.99', {'from': accounts[0]})
    state_machine(StateMachine, accounts, token, voting_escrow)
