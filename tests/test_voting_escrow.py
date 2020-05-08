from .conftest import block_timestamp

WEEK = 7 * 86400


def test_escrow(w3, token, voting_escrow):
    alice, bob = w3.eth.accounts[:2]
    from_alice = {'from': alice}
    # from_bob = {'from': bob}

    alice_amount = 1000 * 10 ** 18
    alice_unlock_time = block_timestamp(w3) + 2 * WEEK
    token.functions.approve(voting_escrow.address, alice_amount).transact(from_alice)
    voting_escrow.functions.deposit(alice_amount, alice_unlock_time).transact(from_alice)
    voting_escrow.functions.withdraw(alice_amount).transact(from_alice)
