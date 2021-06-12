import pytest
from brownie import chain

MONTH = 86400 * 30


@pytest.fixture(scope="module", autouse=True)
def deposit_setup(
    accounts, gauge_controller, minter, liquidity_gauge, unit_gauge, token, mock_lp_token, vault
):
    token.set_minter(minter, {"from": accounts[0]})

    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": accounts[0]})
    gauge_controller.add_gauge(liquidity_gauge, 0, 10 ** 18, {"from": accounts[0]})
    chain.sleep(86400 * 7)

    # transfer tokens
    for acct in accounts[1:4]:
        mock_lp_token.transfer(acct, 1e18, {"from": accounts[0]})

    # approve gauge and wrapper
    for acct in accounts[:4]:
        mock_lp_token.approve(unit_gauge, 2 ** 256 - 1, {"from": acct})
        unit_gauge.approve(vault, 2 ** 256 - 1, {"from": acct})


def test_deposit(alice, unit_gauge, vault):
    unit_gauge.deposit(100000, {"from": alice})
    vault.deposit(25000, {"from": alice})
    assert unit_gauge.balanceOf(alice) == 75000
    assert unit_gauge.depositedBalanceOf(alice) == 25000
    assert unit_gauge.balanceOf(vault) == 25000
    assert unit_gauge.totalSupply() == 100000


def test_deposit_multiple(alice, unit_gauge, vault):
    unit_gauge.deposit(100000, {"from": alice})
    vault.deposit(10000, {"from": alice})
    unit_gauge.deposit(100000, {"from": alice})
    vault.deposit(30000, {"from": alice})
    assert unit_gauge.balanceOf(alice) == 160000
    assert unit_gauge.depositedBalanceOf(alice) == 40000
    assert unit_gauge.balanceOf(vault) == 40000
    assert unit_gauge.totalSupply() == 200000


def test_withdraw_partial(alice, unit_gauge, vault):
    unit_gauge.deposit(100000, {"from": alice})
    vault.deposit(25000, {"from": alice})
    vault.withdraw(15000, {"from": alice})

    assert unit_gauge.balanceOf(alice) == 90000
    assert unit_gauge.depositedBalanceOf(alice) == 10000
    assert unit_gauge.balanceOf(vault) == 10000
    assert unit_gauge.totalSupply() == 100000


def test_withdraw_full(alice, unit_gauge, vault):
    unit_gauge.deposit(100000, {"from": alice})
    vault.deposit(25000, {"from": alice})
    vault.withdraw(25000, {"from": alice})

    assert unit_gauge.balanceOf(alice) == 100000
    assert unit_gauge.depositedBalanceOf(alice) == 0
    assert unit_gauge.balanceOf(vault) == 0
    assert unit_gauge.totalSupply() == 100000


def test_withdraw_multiple(alice, unit_gauge, vault):
    unit_gauge.deposit(100000, {"from": alice})
    vault.deposit(100000, {"from": alice})
    vault.withdraw(15000, {"from": alice})
    vault.withdraw(55000, {"from": alice})

    assert unit_gauge.balanceOf(alice) == 70000
    assert unit_gauge.depositedBalanceOf(alice) == 30000
    assert unit_gauge.balanceOf(vault) == 30000
    assert unit_gauge.totalSupply() == 100000


def test_claim_in_vault(bob, liquidity_gauge, unit_gauge, vault, token):
    unit_gauge.deposit(100000, {"from": bob})
    vault.deposit(100000, {"from": bob})

    chain.sleep(MONTH)
    unit_gauge.claim_tokens({"from": bob})
    expected = liquidity_gauge.integrate_fraction(unit_gauge)

    assert expected > 0
    assert token.balanceOf(bob) == expected


def test_claim_partially_in_vault(bob, liquidity_gauge, unit_gauge, vault, token):
    unit_gauge.deposit(100000, {"from": bob})
    vault.deposit(40000, {"from": bob})

    chain.sleep(MONTH)
    unit_gauge.claim_tokens({"from": bob})
    expected = liquidity_gauge.integrate_fraction(unit_gauge)

    assert expected > 0
    assert token.balanceOf(bob) == expected


def test_claim_multiple_depositors(bob, charlie, liquidity_gauge, unit_gauge, vault, token):
    unit_gauge.deposit(100000, {"from": bob})
    unit_gauge.deposit(100000, {"from": charlie})
    vault.deposit(50000, {"from": bob})

    chain.sleep(MONTH)
    vault.withdraw(50000, {"from": bob})
    unit_gauge.withdraw(100000, {"from": bob})
    vault.deposit(50000, {"from": charlie})

    chain.sleep(MONTH)

    unit_gauge.claim_tokens({"from": bob})
    unit_gauge.claim_tokens({"from": charlie})
    expected = liquidity_gauge.integrate_fraction(unit_gauge)

    assert expected > 0

    balance_bob = token.balanceOf(bob)
    balance_charlie = token.balanceOf(charlie)
    assert (balance_bob * 3 / balance_charlie) == pytest.approx(1)


def test_vault_cannot_claim(bob, liquidity_gauge, unit_gauge, vault, token):
    unit_gauge.deposit(100000, {"from": bob})

    # deposit into vault, and also directly transfer tokens into the vault
    # neither of these scenarios should allow the vault to claim!
    vault.deposit(50000, {"from": bob})
    unit_gauge.transfer(vault, 50000, {"from": bob})

    chain.sleep(MONTH)
    unit_gauge.claim_tokens(vault, {"from": bob})
    expected = liquidity_gauge.integrate_fraction(unit_gauge)

    assert expected > 0
    assert token.balanceOf(vault) == 0


def test_liquidate(bob, charlie, unit_gauge, vault):
    unit_gauge.deposit(100000, {"from": bob})
    vault.deposit(50000, {"from": bob})

    vault.liquidate(bob, 30000, {"from": charlie})

    assert unit_gauge.balanceOf(bob) == 70000
    assert unit_gauge.depositedBalanceOf(bob) == 0
    assert unit_gauge.balanceOf(charlie) == 30000
    assert unit_gauge.depositedBalanceOf(charlie) == 0

    assert unit_gauge.balanceOf(vault) == 0
    assert unit_gauge.totalSupply() == 100000


def test_liquidator_has_balances(bob, charlie, unit_gauge, vault):
    unit_gauge.deposit(100000, {"from": bob})
    unit_gauge.deposit(100000, {"from": charlie})
    vault.deposit(50000, {"from": bob})
    vault.deposit(50000, {"from": charlie})

    vault.liquidate(bob, 30000, {"from": charlie})

    assert unit_gauge.balanceOf(bob) == 70000
    assert unit_gauge.depositedBalanceOf(bob) == 0
    assert unit_gauge.balanceOf(charlie) == 80000
    assert unit_gauge.depositedBalanceOf(charlie) == 50000

    assert unit_gauge.balanceOf(vault) == 50000
    assert unit_gauge.totalSupply() == 200000
