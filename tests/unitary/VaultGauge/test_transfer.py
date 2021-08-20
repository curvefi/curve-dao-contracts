#!/usr/bin/python3
import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(accounts, gauge_controller, distributor, vault_gauge, token, lixir_vault, chain):
    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": accounts[0]})
    gauge_controller.add_gauge(vault_gauge, 0, 0, {"from": accounts[0]})
    
    lixir_vault.deposit(10**18 / 2, 10**18 /2, 0, 0, accounts[0], chain.time() + 10**18, {"from": accounts[0]})
    lixir_vault.approve(vault_gauge, 2 ** 256 - 1, {"from": accounts[0]})
    vault_gauge.deposit(10 ** 18, {"from": accounts[0]})


def test_sender_balance_decreases(accounts, vault_gauge):
    sender_balance = vault_gauge.balanceOf(accounts[0])
    amount = sender_balance // 4

    vault_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert vault_gauge.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, vault_gauge):
    receiver_balance = vault_gauge.balanceOf(accounts[1])
    amount = vault_gauge.balanceOf(accounts[0]) // 4

    vault_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert vault_gauge.balanceOf(accounts[1]) == receiver_balance + amount


def test_total_supply_not_affected(accounts, vault_gauge):
    total_supply = vault_gauge.totalSupply()
    amount = vault_gauge.balanceOf(accounts[0])

    vault_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert vault_gauge.totalSupply() == total_supply


def test_returns_true(accounts, vault_gauge):
    amount = vault_gauge.balanceOf(accounts[0])
    tx = vault_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, vault_gauge):
    amount = vault_gauge.balanceOf(accounts[0])
    receiver_balance = vault_gauge.balanceOf(accounts[1])

    vault_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert vault_gauge.balanceOf(accounts[0]) == 0
    assert vault_gauge.balanceOf(accounts[1]) == receiver_balance + amount


def test_transfer_zero_tokens(accounts, vault_gauge):
    sender_balance = vault_gauge.balanceOf(accounts[0])
    receiver_balance = vault_gauge.balanceOf(accounts[1])

    vault_gauge.transfer(accounts[1], 0, {"from": accounts[0]})

    assert vault_gauge.balanceOf(accounts[0]) == sender_balance
    assert vault_gauge.balanceOf(accounts[1]) == receiver_balance


def test_transfer_to_self(accounts, vault_gauge):
    sender_balance = vault_gauge.balanceOf(accounts[0])
    amount = sender_balance // 4

    vault_gauge.transfer(accounts[0], amount, {"from": accounts[0]})

    assert vault_gauge.balanceOf(accounts[0]) == sender_balance


def test_insufficient_balance(accounts, vault_gauge):
    balance = vault_gauge.balanceOf(accounts[0])

    with brownie.reverts():
        vault_gauge.transfer(accounts[1], balance + 1, {"from": accounts[0]})


def test_transfer_event_fires(accounts, vault_gauge):
    amount = vault_gauge.balanceOf(accounts[0])
    tx = vault_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.events["Transfer"].values() == [accounts[0], accounts[1], amount]
