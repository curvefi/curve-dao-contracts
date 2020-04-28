from random import random, randrange
from .conftest import YEAR, time_travel


def test_test(w3, mock_lp_token, token, liquidity_gauge):
    alice, bob = w3.eth.accounts[:2]
    from_alice = {'from': alice}
    from_bob = {'from': bob}

    # Let Alice and Bob have about the same token amount
    mock_lp_token.functions.transfer(
            bob, mock_lp_token.caller.balanceOf(alice) // 2
    ).transact(from_alice)

    # Now let's have a loop where Bob always deposit or withdraws,
    # and Alice does so more rarely
    for i in range(20):
        is_alice = (random() < 0.2)
        dt = randrange(1, YEAR // 5)
        time_travel(w3, dt)

        # For Bob
        is_withdraw = (i > 0) * (random() < 0.5)
        if is_withdraw:
            amount = randrange(1, liquidity_gauge.caller.balanceOf(bob) + 1)
            liquidity_gauge.functions.withdraw(amount).transact(from_bob)
        else:
            amount = randrange(1, mock_lp_token.caller.balanceOf(bob) // 10 + 1)
            mock_lp_token.functions.approve(liquidity_gauge.address, amount).transact(from_bob)
            liquidity_gauge.functions.deposit(amount).transact(from_bob)

        if is_alice:
            # For Alice
            is_withdraw_alice = (liquidity_gauge.caller.balanceOf(alice) > 0) * (random() < 0.5)

            if is_withdraw_alice:
                amount_alice = randrange(1, liquidity_gauge.caller.balanceOf(alice) // 10 + 1)
                liquidity_gauge.functions.withdraw(amount).transact(from_bob)
            else:
                amount_alice = randrange(1, mock_lp_token.caller.balanceOf(alice) + 1)
                mock_lp_token.functions.approve(liquidity_gauge.address, amount_alice).transact(from_alice)
                liquidity_gauge.functions.deposit(amount_alice).transact(from_alice)
