import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def deposit_setup(accounts, vault_gauge, lixir_vault, chain):
    lixir_vault.deposit(10**18 / 2, 10**18 /2, 0, 0, accounts[0], chain.time() + 10**18, {"from": accounts[0]})
    lixir_vault.approve(vault_gauge, 2 ** 256 - 1, {"from": accounts[0]})


def test_deposit(accounts, vault_gauge, lixir_vault):
    balance = lixir_vault.balanceOf(accounts[0])
    vault_gauge.deposit(100000, {"from": accounts[0]})

    assert lixir_vault.balanceOf(vault_gauge) == 100000
    assert lixir_vault.balanceOf(accounts[0]) == balance - 100000
    assert vault_gauge.totalSupply() == 100000
    assert vault_gauge.balanceOf(accounts[0]) == 100000


def test_deposit_zero(accounts, vault_gauge, lixir_vault):
    balance = lixir_vault.balanceOf(accounts[0])
    vault_gauge.deposit(0, {"from": accounts[0]})

    assert lixir_vault.balanceOf(vault_gauge) == 0
    assert lixir_vault.balanceOf(accounts[0]) == balance
    assert vault_gauge.totalSupply() == 0
    assert vault_gauge.balanceOf(accounts[0]) == 0


def test_deposit_insufficient_balance(accounts, vault_gauge, lixir_vault):
    with brownie.reverts():
        vault_gauge.deposit(100000, {"from": accounts[1]})


def test_withdraw(accounts, vault_gauge, lixir_vault):
    balance = lixir_vault.balanceOf(accounts[0])

    vault_gauge.deposit(100000, {"from": accounts[0]})
    vault_gauge.withdraw(100000, {"from": accounts[0]})

    assert lixir_vault.balanceOf(vault_gauge) == 0
    assert lixir_vault.balanceOf(accounts[0]) == balance
    assert vault_gauge.totalSupply() == 0
    assert vault_gauge.balanceOf(accounts[0]) == 0


def test_withdraw_zero(accounts, vault_gauge, lixir_vault):
    balance = lixir_vault.balanceOf(accounts[0])
    vault_gauge.deposit(100000, {"from": accounts[0]})
    vault_gauge.withdraw(0, {"from": accounts[0]})

    assert lixir_vault.balanceOf(vault_gauge) == 100000
    assert lixir_vault.balanceOf(accounts[0]) == balance - 100000
    assert vault_gauge.totalSupply() == 100000
    assert vault_gauge.balanceOf(accounts[0]) == 100000


def test_withdraw_new_epoch(accounts, chain, vault_gauge, lixir_vault):
    balance = lixir_vault.balanceOf(accounts[0])

    vault_gauge.deposit(100000, {"from": accounts[0]})
    chain.sleep(86400 * 400)
    vault_gauge.withdraw(100000, {"from": accounts[0]})

    assert lixir_vault.balanceOf(vault_gauge) == 0
    assert lixir_vault.balanceOf(accounts[0]) == balance
    assert vault_gauge.totalSupply() == 0
    assert vault_gauge.balanceOf(accounts[0]) == 0
