#!/usr/bin/python3
import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(accounts, gauge_controller, minter, liquidity_gauge, unit_gauge, token, mock_lp_token):
    token.set_minter(minter, {"from": accounts[0]})

    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": accounts[0]})
    gauge_controller.add_gauge(liquidity_gauge, 0, 0, {"from": accounts[0]})

    mock_lp_token.approve(unit_gauge, 2 ** 256 - 1, {"from": accounts[0]})
    unit_gauge.deposit(10 ** 18, {"from": accounts[0]})


def test_sender_balance_decreases(accounts, unit_gauge):
    sender_balance = unit_gauge.balanceOf(accounts[0])
    amount = sender_balance // 4

    unit_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert unit_gauge.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, unit_gauge):
    receiver_balance = unit_gauge.balanceOf(accounts[1])
    amount = unit_gauge.balanceOf(accounts[0]) // 4

    unit_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert unit_gauge.balanceOf(accounts[1]) == receiver_balance + amount


def test_total_supply_not_affected(accounts, unit_gauge):
    total_supply = unit_gauge.totalSupply()
    amount = unit_gauge.balanceOf(accounts[0])

    unit_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert unit_gauge.totalSupply() == total_supply


def test_returns_true(accounts, unit_gauge):
    amount = unit_gauge.balanceOf(accounts[0])
    tx = unit_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, unit_gauge):
    amount = unit_gauge.balanceOf(accounts[0])
    receiver_balance = unit_gauge.balanceOf(accounts[1])

    unit_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert unit_gauge.balanceOf(accounts[0]) == 0
    assert unit_gauge.balanceOf(accounts[1]) == receiver_balance + amount


def test_transfer_zero_tokens(accounts, unit_gauge):
    sender_balance = unit_gauge.balanceOf(accounts[0])
    receiver_balance = unit_gauge.balanceOf(accounts[1])

    unit_gauge.transfer(accounts[1], 0, {"from": accounts[0]})

    assert unit_gauge.balanceOf(accounts[0]) == sender_balance
    assert unit_gauge.balanceOf(accounts[1]) == receiver_balance


def test_transfer_to_self(accounts, unit_gauge):
    sender_balance = unit_gauge.balanceOf(accounts[0])
    amount = sender_balance // 4

    unit_gauge.transfer(accounts[0], amount, {"from": accounts[0]})

    assert unit_gauge.balanceOf(accounts[0]) == sender_balance


def test_insufficient_balance(accounts, unit_gauge):
    balance = unit_gauge.balanceOf(accounts[0])

    with brownie.reverts():
        unit_gauge.transfer(accounts[1], balance + 1, {"from": accounts[0]})


def test_transfer_event_fires(accounts, unit_gauge):
    amount = unit_gauge.balanceOf(accounts[0])
    tx = unit_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.events["Transfer"].values() == [accounts[0], accounts[1], amount]
