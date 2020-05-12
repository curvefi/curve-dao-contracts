import pytest
from eth_tester.exceptions import TransactionFailed
from .conftest import block_timestamp, time_travel

WEEK = 7 * 86400


def test_escrow_desposit_withdraw(w3, token, voting_escrow):
    alice, bob = w3.eth.accounts[:2]
    from_alice = {'from': alice}
    # from_bob = {'from': bob}

    alice_amount = 1000 * 10 ** 18
    alice_unlock_time = (block_timestamp(w3) + 2 * WEEK) // WEEK * WEEK
    token.functions.approve(voting_escrow.address, alice_amount * 10).transact(from_alice)

    # Simple deposit / withdraw
    voting_escrow.functions.deposit(alice_amount, alice_unlock_time).transact(from_alice)
    with pytest.raises(TransactionFailed):
        voting_escrow.functions.withdraw(alice_amount).transact(from_alice)
    time_travel(w3, 2 * WEEK)
    voting_escrow.functions.withdraw(alice_amount).transact(from_alice)
    with pytest.raises(TransactionFailed):
        voting_escrow.functions.withdraw(1).transact(from_alice)

    # Deposit, add more, withdraw all
    alice_unlock_time = (block_timestamp(w3) + 2 * WEEK) // WEEK * WEEK
    voting_escrow.functions.deposit(alice_amount, alice_unlock_time).transact(from_alice)
    time_travel(w3, WEEK)
    with pytest.raises(TransactionFailed):
        voting_escrow.functions.deposit(alice_amount, alice_unlock_time - 1).transact(from_alice)
    voting_escrow.functions.deposit(alice_amount).transact(from_alice)
    time_travel(w3, WEEK)
    voting_escrow.functions.withdraw(2 * alice_amount).transact(from_alice)
