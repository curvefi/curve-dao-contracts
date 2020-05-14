import brownie

WEEK = 7 * 86400


def test_escrow_desposit_withdraw(rpc, accounts, token, voting_escrow, block_timestamp):
    alice, bob = accounts[:2]
    from_alice = {'from': alice}
    # from_bob = {'from': bob}

    alice_amount = 1000 * 10 ** 18
    alice_unlock_time = (block_timestamp() + 2 * WEEK) // WEEK * WEEK
    token.approve(voting_escrow.address, alice_amount * 10, from_alice)

    # Simple deposit / withdraw
    voting_escrow.deposit(alice_amount, alice_unlock_time, from_alice)
    with brownie.reverts():
        voting_escrow.withdraw(alice_amount, from_alice)
    rpc.sleep(2 * WEEK)
    rpc.mine()
    voting_escrow.withdraw(alice_amount, from_alice)
    with brownie.reverts():
        voting_escrow.withdraw(1, from_alice)

    # Deposit, add more, withdraw all
    alice_unlock_time = (block_timestamp() + 2 * WEEK) // WEEK * WEEK
    voting_escrow.deposit(alice_amount, alice_unlock_time, from_alice)
    rpc.sleep(WEEK)
    rpc.mine()
    with brownie.reverts():
        voting_escrow.deposit(alice_amount, alice_unlock_time - 1, from_alice)
    voting_escrow.deposit(alice_amount, from_alice)
    rpc.sleep(WEEK)
    rpc.mine()
    voting_escrow.withdraw(2 * alice_amount, from_alice)
