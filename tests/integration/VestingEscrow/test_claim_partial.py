import pytest
from brownie.test import given, strategy

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def initial_funding(vesting, accounts):
    vesting.add_tokens(10 ** 21, {"from": accounts[0]})
    recipients = [accounts[1]] + [ZERO_ADDRESS] * 99
    vesting.fund(recipients, [10 ** 20] + [0] * 99, {"from": accounts[0]})


@given(sleep_time=strategy("uint", max_value=100000))
def test_claim_partial(vesting, coin_a, accounts, chain, start_time, sleep_time, end_time):
    chain.sleep(start_time - chain.time() + sleep_time)
    tx = vesting.claim({"from": accounts[1]})
    expected_amount = 10 ** 20 * (tx.timestamp - start_time) // (end_time - start_time)

    assert coin_a.balanceOf(accounts[1]) == expected_amount
