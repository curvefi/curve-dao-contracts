ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_disable_after_end_time(vesting_simple, coin_a, accounts, chain, end_time):
    chain.sleep(end_time - chain.time())
    vesting_simple.toggle_disable(accounts[1], {'from': accounts[0]})
    vesting_simple.claim({'from': accounts[1]})

    assert coin_a.balanceOf(accounts[1]) == 10**20


def test_disable_before_start_time(vesting_simple, coin_a, accounts, chain, end_time):
    vesting_simple.toggle_disable(accounts[1], {'from': accounts[0]})
    chain.sleep(end_time - chain.time())
    vesting_simple.claim({'from': accounts[1]})

    assert coin_a.balanceOf(accounts[1]) == 0


def test_disable_before_start_time_and_reenable(vesting_simple, coin_a, accounts, chain, end_time):
    vesting_simple.toggle_disable(accounts[1], {'from': accounts[0]})
    chain.sleep(end_time - chain.time())
    vesting_simple.toggle_disable(accounts[1], {'from': accounts[0]})
    vesting_simple.claim({'from': accounts[1]})

    assert coin_a.balanceOf(accounts[1]) == 10**20


def test_disable_partially_unvested(vesting_simple, coin_a, accounts, chain, start_time, end_time):
    chain.sleep(start_time - chain.time() + 31337)
    tx = vesting_simple.toggle_disable(accounts[1], {'from': accounts[0]})
    chain.sleep(end_time - chain.time())
    vesting_simple.claim({'from': accounts[1]})

    expected_amount = 10**20 * (tx.timestamp - start_time) // (end_time - start_time)
    assert coin_a.balanceOf(accounts[1]) == expected_amount
    assert vesting_simple.total_claimed(accounts[1]) == expected_amount


def test_disable_multiple_partial(vesting_simple, coin_a, accounts, chain, start_time, end_time):
    chain.sleep(start_time - chain.time() + 31337)
    vesting_simple.toggle_disable(accounts[1], {'from': accounts[0]})
    chain.sleep(31337)
    vesting_simple.claim({'from': accounts[1]})
    vesting_simple.toggle_disable(accounts[1], {'from': accounts[0]})
    tx = vesting_simple.toggle_disable(accounts[1], {'from': accounts[0]})
    chain.sleep(end_time - chain.time())
    vesting_simple.claim({'from': accounts[1]})

    expected_amount = 10**20 * (tx.timestamp - start_time) // (end_time - start_time)
    assert coin_a.balanceOf(accounts[1]) == expected_amount
    assert vesting_simple.total_claimed(accounts[1]) == expected_amount
