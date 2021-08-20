#!/usr/bin/python3
import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(accounts, gauge_controller, distributor, vault_gauge, token, lixir_vault, chain):
    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": accounts[0]})
    gauge_controller.add_gauge(vault_gauge, 0, 0, {"from": accounts[0]})


def test_sender_balance_decreases(accounts, vault_gauge):
    sender_balance = vault_gauge.balanceOf(accounts[0])
    amount = sender_balance // 4

    vault_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    vault_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert vault_gauge.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, vault_gauge):
    receiver_balance = vault_gauge.balanceOf(accounts[2])
    amount = vault_gauge.balanceOf(accounts[0]) // 4

    vault_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    vault_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert vault_gauge.balanceOf(accounts[2]) == receiver_balance + amount


def test_caller_balance_not_affected(accounts, vault_gauge):
    caller_balance = vault_gauge.balanceOf(accounts[1])
    amount = vault_gauge.balanceOf(accounts[0])

    vault_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    vault_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert vault_gauge.balanceOf(accounts[1]) == caller_balance


def test_caller_approval_affected(accounts, vault_gauge):
    approval_amount = vault_gauge.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    vault_gauge.approve(accounts[1], approval_amount, {"from": accounts[0]})
    vault_gauge.transferFrom(accounts[0], accounts[2], transfer_amount, {"from": accounts[1]})

    assert vault_gauge.allowance(accounts[0], accounts[1]) == approval_amount - transfer_amount


def test_receiver_approval_not_affected(accounts, vault_gauge):
    approval_amount = vault_gauge.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    vault_gauge.approve(accounts[1], approval_amount, {"from": accounts[0]})
    vault_gauge.approve(accounts[2], approval_amount, {"from": accounts[0]})
    vault_gauge.transferFrom(accounts[0], accounts[2], transfer_amount, {"from": accounts[1]})

    assert vault_gauge.allowance(accounts[0], accounts[2]) == approval_amount


def test_total_supply_not_affected(accounts, vault_gauge):
    total_supply = vault_gauge.totalSupply()
    amount = vault_gauge.balanceOf(accounts[0])

    vault_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    vault_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert vault_gauge.totalSupply() == total_supply


def test_returns_true(accounts, vault_gauge):
    amount = vault_gauge.balanceOf(accounts[0])
    vault_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    tx = vault_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, vault_gauge):
    amount = vault_gauge.balanceOf(accounts[0])
    receiver_balance = vault_gauge.balanceOf(accounts[2])

    vault_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    vault_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert vault_gauge.balanceOf(accounts[0]) == 0
    assert vault_gauge.balanceOf(accounts[2]) == receiver_balance + amount


def test_transfer_zero_tokens(accounts, vault_gauge):
    sender_balance = vault_gauge.balanceOf(accounts[0])
    receiver_balance = vault_gauge.balanceOf(accounts[2])

    vault_gauge.approve(accounts[1], sender_balance, {"from": accounts[0]})
    vault_gauge.transferFrom(accounts[0], accounts[2], 0, {"from": accounts[1]})

    assert vault_gauge.balanceOf(accounts[0]) == sender_balance
    assert vault_gauge.balanceOf(accounts[2]) == receiver_balance


def test_transfer_zero_tokens_without_approval(accounts, vault_gauge):
    sender_balance = vault_gauge.balanceOf(accounts[0])
    receiver_balance = vault_gauge.balanceOf(accounts[2])

    vault_gauge.transferFrom(accounts[0], accounts[2], 0, {"from": accounts[1]})

    assert vault_gauge.balanceOf(accounts[0]) == sender_balance
    assert vault_gauge.balanceOf(accounts[2]) == receiver_balance


def test_insufficient_balance(accounts, vault_gauge):
    balance = vault_gauge.balanceOf(accounts[0])

    vault_gauge.approve(accounts[1], balance + 1, {"from": accounts[0]})
    with brownie.reverts():
        vault_gauge.transferFrom(accounts[0], accounts[2], balance + 1, {"from": accounts[1]})


def test_insufficient_approval(accounts, vault_gauge):
    balance = vault_gauge.balanceOf(accounts[0])

    vault_gauge.approve(accounts[1], balance - 1, {"from": accounts[0]})
    with brownie.reverts():
        vault_gauge.transferFrom(accounts[0], accounts[2], balance, {"from": accounts[1]})


def test_no_approval(accounts, vault_gauge):
    balance = vault_gauge.balanceOf(accounts[0])

    with brownie.reverts():
        vault_gauge.transferFrom(accounts[0], accounts[2], balance, {"from": accounts[1]})


def test_infinite_approval(accounts, vault_gauge):
    vault_gauge.approve(accounts[1], 2 ** 256 - 1, {"from": accounts[0]})
    vault_gauge.transferFrom(accounts[0], accounts[2], 10000, {"from": accounts[1]})

    assert vault_gauge.allowance(accounts[0], accounts[1]) == 2 ** 256 - 1


def test_revoked_approval(accounts, vault_gauge):
    balance = vault_gauge.balanceOf(accounts[0])

    vault_gauge.approve(accounts[1], balance, {"from": accounts[0]})
    vault_gauge.approve(accounts[1], 0, {"from": accounts[0]})

    with brownie.reverts():
        vault_gauge.transferFrom(accounts[0], accounts[2], balance, {"from": accounts[1]})


def test_transfer_to_self(accounts, vault_gauge):
    sender_balance = vault_gauge.balanceOf(accounts[0])
    amount = sender_balance // 4

    vault_gauge.approve(accounts[0], sender_balance, {"from": accounts[0]})
    vault_gauge.transferFrom(accounts[0], accounts[0], amount, {"from": accounts[0]})

    assert vault_gauge.balanceOf(accounts[0]) == sender_balance
    assert vault_gauge.allowance(accounts[0], accounts[0]) == sender_balance - amount


def test_transfer_to_self_no_approval(accounts, vault_gauge):
    amount = vault_gauge.balanceOf(accounts[0])

    with brownie.reverts():
        vault_gauge.transferFrom(accounts[0], accounts[0], amount, {"from": accounts[0]})


def test_transfer_event_fires(accounts, vault_gauge):
    amount = vault_gauge.balanceOf(accounts[0])

    vault_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    tx = vault_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert tx.events["Transfer"].values() == [accounts[0], accounts[2], amount]
