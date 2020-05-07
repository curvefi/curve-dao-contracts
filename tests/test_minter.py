import pytest
from eth_tester.exceptions import TransactionFailed
from .conftest import time_travel


def to_int(*args):
    # Helper function for readability
    return [int(a) for a in args]


def test_mint(tester, w3, mock_lp_token, gauge_controller, three_gauges, minter, token):
    admin, bob, charlie, dan = w3.eth.accounts[:4]
    from_admin = {'from': admin}

    token.functions.set_minter(minter.address).transact(from_admin)

    W = 10 ** 18
    amount = 10 ** 18
    type_weights = to_int(0.5 * W, 2 * W)
    gauge_weights = to_int(2 * W, 1 * W, 0.5 * W)
    gauge_types = [0, 0, 1]

    # Set up types
    for i, w in enumerate(type_weights):
        gauge_controller.functions.add_type().transact(from_admin)
        gauge_controller.functions.change_type_weight(i, w).transact(from_admin)

    # Set up gauges
    for g, t, w in zip(three_gauges, gauge_types, gauge_weights):
        gauge_controller.functions.add_gauge(g.address, t, w).transact(from_admin)

    # Transfer tokens to Bob, Charlie and Dan
    for user in w3.eth.accounts[1:4]:
        mock_lp_token.functions.transfer(user, amount).transact(from_admin)

    # Bob and Charlie deposit to gauges with different weights
    mock_lp_token.functions.approve(three_gauges[1].address, amount).transact({'from': bob})
    three_gauges[1].functions.deposit(amount).transact({'from': bob})
    mock_lp_token.functions.approve(three_gauges[2].address, amount).transact({'from': charlie})
    three_gauges[2].functions.deposit(amount).transact({'from': charlie})

    dt = 30 * 86400
    time_travel(w3, dt)
    tester.mine_block()

    mock_lp_token.functions.approve(three_gauges[1].address, amount).transact({'from': dan})
    three_gauges[1].functions.deposit(amount).transact({'from': dan})
    time_travel(w3, dt)
    tester.mine_block()

    with pytest.raises(TransactionFailed):
        # Cannot withdraw too much
        three_gauges[1].functions.withdraw(amount + 1).transact({'from': bob})

    # Withdraw
    three_gauges[1].functions.withdraw(amount).transact({'from': bob})
    three_gauges[2].functions.withdraw(amount).transact({'from': charlie})
    three_gauges[1].functions.withdraw(amount).transact({'from': dan})

    for user in w3.eth.accounts[1:4]:
        assert mock_lp_token.caller.balanceOf(user) == amount

    # Claim for Bob now
    minter.functions.mint(1).transact({'from': bob})
    bob_tokens = token.caller.balanceOf(bob)

    time_travel(w3, dt)

    minter.functions.mint(1).transact({'from': bob})  # This won't give anything
    assert bob_tokens == token.caller.balanceOf(bob)

    minter.functions.mint(2).transact({'from': charlie})
    charlie_tokens = token.caller.balanceOf(charlie)
    minter.functions.mint(1).transact({'from': dan})
    dan_tokens = token.caller.balanceOf(dan)

    S = bob_tokens + charlie_tokens + dan_tokens
    ww = [w * type_weights[t] for w, t in zip(gauge_weights, gauge_types)]
    Sw = ww[1] + ww[2]  # Gauge 0 not used

    # Bob was in gauge 1 for half the time
    # Charlie and Dan were there for full time, gauges 2 and 1
    assert bob_tokens / S == 0.25 * ww[1] / Sw
    assert charlie_tokens / S == ww[2] / Sw
    assert dan_tokens / S == 0.75 * ww[1] / Sw
