import itertools

import pytest

TYPE_WEIGHTS = [5e17, 1e19]
GAUGE_WEIGHTS = [1e19, 1e18, 5e17]
GAUGE_TYPES = [0, 0, 1]

MONTH = 86400 * 30
WEEK = 7 * 86400


@pytest.fixture(scope="module", autouse=True)
def setup(
    accounts, mock_lp_token, token, minter, gauge_controller, liquidity_gauge, gauge_wrapper,
):
    token.set_minter(minter, {"from": accounts[0]})

    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": accounts[0]})
    gauge_controller.add_gauge(liquidity_gauge, 0, 10 ** 18, {"from": accounts[0]})

    # transfer tokens
    for acct in accounts[1:4]:
        mock_lp_token.transfer(acct, 1e18, {"from": accounts[0]})

    # approve gauge and wrapper
    for gauge, acct in itertools.product([liquidity_gauge, gauge_wrapper], accounts[1:4]):
        mock_lp_token.approve(gauge, 1e18, {"from": acct})


def test_claim(accounts, chain, liquidity_gauge, gauge_wrapper, token):
    gauge_wrapper.deposit(1e18, {"from": accounts[1]})

    chain.sleep(MONTH)
    gauge_wrapper.claim_tokens({"from": accounts[1]})
    expected = liquidity_gauge.integrate_fraction(gauge_wrapper)

    assert expected > 0
    assert token.balanceOf(accounts[1]) == expected


def test_multiple_depositors(accounts, chain, liquidity_gauge, gauge_wrapper, token):
    gauge_wrapper.deposit(1e18, {"from": accounts[1]})

    chain.sleep(MONTH)
    gauge_wrapper.deposit(1e18, {"from": accounts[2]})
    chain.sleep(MONTH)
    gauge_wrapper.withdraw(1e18, {"from": accounts[1]})
    gauge_wrapper.withdraw(1e18, {"from": accounts[2]})
    chain.sleep(10)

    gauge_wrapper.claim_tokens({"from": accounts[1]})
    gauge_wrapper.claim_tokens({"from": accounts[2]})

    expected = liquidity_gauge.integrate_fraction(gauge_wrapper)
    actual = token.balanceOf(accounts[1]) + token.balanceOf(accounts[2])

    assert expected > 0
    assert 0 <= expected - actual <= 1


def test_multiple_claims(accounts, chain, liquidity_gauge, gauge_wrapper, token):
    gauge_wrapper.deposit(1e18, {"from": accounts[1]})

    chain.sleep(MONTH)
    gauge_wrapper.claim_tokens({"from": accounts[1]})
    balance = token.balanceOf(accounts[1])

    chain.sleep(MONTH)
    gauge_wrapper.claim_tokens({"from": accounts[1]})
    expected = liquidity_gauge.integrate_fraction(gauge_wrapper)
    final_balance = token.balanceOf(accounts[1])

    assert final_balance > balance
    assert final_balance == expected


def test_claim_without_deposit(accounts, chain, gauge_wrapper, token):
    gauge_wrapper.claim_tokens({"from": accounts[1]})

    assert token.balanceOf(accounts[1]) == 0


def test_claimable_no_deposit(accounts, gauge_wrapper):
    assert gauge_wrapper.claimable_tokens.call(accounts[1]) == 0


def test_claimable_tokens(accounts, chain, gauge_wrapper, token):
    gauge_wrapper.deposit(1e18, {"from": accounts[1]})

    chain.sleep(MONTH)
    chain.mine()
    claimable = gauge_wrapper.claimable_tokens.call(accounts[1])

    gauge_wrapper.claim_tokens({"from": accounts[1]})
    assert token.balanceOf(accounts[1]) >= claimable > 0
