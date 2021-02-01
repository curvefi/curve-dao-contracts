ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_claim_full(vesting_simple, coin_a, accounts, chain, end_time):
    chain.sleep(end_time - chain.time())
    vesting_simple.claim({"from": accounts[1]})

    assert coin_a.balanceOf(accounts[1]) == 10 ** 20


def test_claim_for_another(vesting_simple, coin_a, accounts, chain, end_time):
    chain.sleep(end_time - chain.time())
    vesting_simple.claim(accounts[1], {"from": accounts[2]})

    assert coin_a.balanceOf(accounts[1]) == 10 ** 20


def test_claim_for_self(vesting_simple, coin_a, accounts, chain, end_time):
    chain.sleep(end_time - chain.time())
    vesting_simple.claim(accounts[1], {"from": accounts[1]})

    assert coin_a.balanceOf(accounts[1]) == 10 ** 20


def test_claim_before_start(vesting_simple, coin_a, accounts, chain, start_time):
    chain.sleep(start_time - chain.time() - 5)
    vesting_simple.claim({"from": accounts[1]})

    assert coin_a.balanceOf(accounts[1]) == 0


def test_claim_partial(vesting_simple, coin_a, accounts, chain, start_time, end_time):
    chain.sleep(start_time - chain.time() + 31337)
    tx = vesting_simple.claim({"from": accounts[1]})
    expected_amount = 10 ** 20 * (tx.timestamp - start_time) // (end_time - start_time)

    assert coin_a.balanceOf(accounts[1]) == expected_amount
    assert vesting_simple.total_claimed(accounts[1]) == expected_amount


def test_claim_multiple(vesting_simple, coin_a, accounts, chain, start_time, end_time):
    chain.sleep(start_time - chain.time() - 1000)
    balance = 0
    for i in range(11):
        chain.sleep((end_time - start_time) // 10)
        vesting_simple.claim({"from": accounts[1]})
        new_balance = coin_a.balanceOf(accounts[1])
        assert new_balance > balance
        balance = new_balance

    assert coin_a.balanceOf(accounts[1]) == 10 ** 20
