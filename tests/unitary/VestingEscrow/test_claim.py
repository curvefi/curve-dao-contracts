import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def initial_funding(vesting, accounts):
    recipients = [accounts[1]] + [ZERO_ADDRESS] * 9
    vesting.fund(recipients, [10**20] + [0] * 9, {'from': accounts[0]})


def test_claim_full(vesting, coin_a, accounts, chain, end_time):
    chain.sleep(end_time - chain.time())
    vesting.claim({'from': accounts[1]})

    assert coin_a.balanceOf(accounts[1]) == 10**20


def test_claim_for_another(vesting, coin_a, accounts, chain, end_time):
    chain.sleep(end_time - chain.time())
    vesting.claim(accounts[1], {'from': accounts[2]})

    assert coin_a.balanceOf(accounts[1]) == 10**20


def test_claim_for_self(vesting, coin_a, accounts, chain, end_time):
    chain.sleep(end_time - chain.time())
    vesting.claim(accounts[1], {'from': accounts[1]})

    assert coin_a.balanceOf(accounts[1]) == 10**20


def test_claim_before_start(vesting, coin_a, accounts, chain, start_time):
    chain.sleep(start_time - chain.time() - 5)
    vesting.claim({'from': accounts[1]})

    assert coin_a.balanceOf(accounts[1]) == 0


def test_claim_partial(vesting, coin_a, accounts, chain, start_time, end_time):
    chain.sleep(start_time - chain.time() + 31337)
    tx = vesting.claim({'from': accounts[1]})
    expected_amount = 10**20 * (tx.timestamp - start_time) // (end_time - start_time)

    assert coin_a.balanceOf(accounts[1]) == expected_amount
    assert vesting.total_claimed(accounts[1]) == expected_amount


def test_claim_multiple(vesting, coin_a, accounts, chain):
    for i in range(11):
        chain.sleep(10000)
        vesting.claim({'from': accounts[1]})

    assert coin_a.balanceOf(accounts[1]) == 10**20
