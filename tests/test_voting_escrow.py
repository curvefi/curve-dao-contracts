
WEEK = 7 * 86400


def test_deposit(accounts, rpc, token, voting_escrow):
    alice, bob = accounts[:2]

    alice_amount = 1000 * 10 ** 18
    alice_unlock_time = rpc.time() + 2 * WEEK

    token.approve(voting_escrow, alice_amount, {'from': alice})

    voting_escrow.deposit(alice_amount, alice_unlock_time, {'from': alice})
    voting_escrow.withdraw(alice_amount, {'from': alice})
