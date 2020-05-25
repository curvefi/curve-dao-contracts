from brownie.test import contract_strategy  # , strategy


class StateMachine:
    st_escrow = contract_strategy("VotingEscrow")
    st_token = contract_strategy("ERC20CRV")

    def __init__(self, accounts, token, voting_escrow):
        self.accounts = accounts

        # account[0] has the bank: give a million to everyone
        amount = 10 ** 6 * 10 ** 18
        _from = accounts[0]
        for _to in accounts[1:]:
            token.transfer(_to, amount, {'from': _from})

        # Infinite approvals for voting escrow
        for addr in accounts:
            token.approve(voting_escrow.address, 2 ** 256 - 1, {'from': addr})

    def rule_dummy(self):
        pass


def test_state_machine(state_machine, accounts, token, voting_escrow):
    state_machine(StateMachine, accounts, token, voting_escrow)
