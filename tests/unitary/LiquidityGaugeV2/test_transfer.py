#!/usr/bin/python3
import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(accounts, gauge_controller, minter, gauge_v2, token, mock_lp_token):
    token.set_minter(minter, {"from": accounts[0]})

    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": accounts[0]})
    gauge_controller.add_gauge(gauge_v2, 0, 0, {"from": accounts[0]})

    mock_lp_token.approve(gauge_v2, 2 ** 256 - 1, {"from": accounts[0]})
    gauge_v2.deposit(10 ** 18, {"from": accounts[0]})


def test_sender_balance_decreases(accounts, gauge_v2):
    sender_balance = gauge_v2.balanceOf(accounts[0])
    amount = sender_balance // 4

    gauge_v2.transfer(accounts[1], amount, {"from": accounts[0]})

    assert gauge_v2.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, gauge_v2):
    receiver_balance = gauge_v2.balanceOf(accounts[1])
    amount = gauge_v2.balanceOf(accounts[0]) // 4

    gauge_v2.transfer(accounts[1], amount, {"from": accounts[0]})

    assert gauge_v2.balanceOf(accounts[1]) == receiver_balance + amount


def test_total_supply_not_affected(accounts, gauge_v2):
    total_supply = gauge_v2.totalSupply()
    amount = gauge_v2.balanceOf(accounts[0])

    gauge_v2.transfer(accounts[1], amount, {"from": accounts[0]})

    assert gauge_v2.totalSupply() == total_supply


def test_returns_true(accounts, gauge_v2):
    amount = gauge_v2.balanceOf(accounts[0])
    tx = gauge_v2.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, gauge_v2):
    amount = gauge_v2.balanceOf(accounts[0])
    receiver_balance = gauge_v2.balanceOf(accounts[1])

    gauge_v2.transfer(accounts[1], amount, {"from": accounts[0]})

    assert gauge_v2.balanceOf(accounts[0]) == 0
    assert gauge_v2.balanceOf(accounts[1]) == receiver_balance + amount


def test_transfer_zero_tokens(accounts, gauge_v2):
    sender_balance = gauge_v2.balanceOf(accounts[0])
    receiver_balance = gauge_v2.balanceOf(accounts[1])

    gauge_v2.transfer(accounts[1], 0, {"from": accounts[0]})

    assert gauge_v2.balanceOf(accounts[0]) == sender_balance
    assert gauge_v2.balanceOf(accounts[1]) == receiver_balance


def test_transfer_to_self(accounts, gauge_v2):
    sender_balance = gauge_v2.balanceOf(accounts[0])
    amount = sender_balance // 4

    gauge_v2.transfer(accounts[0], amount, {"from": accounts[0]})

    assert gauge_v2.balanceOf(accounts[0]) == sender_balance


def test_insufficient_balance(accounts, gauge_v2):
    balance = gauge_v2.balanceOf(accounts[0])

    with brownie.reverts():
        gauge_v2.transfer(accounts[1], balance + 1, {"from": accounts[0]})


def test_transfer_event_fires(accounts, gauge_v2):
    amount = gauge_v2.balanceOf(accounts[0])
    tx = gauge_v2.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.events["Transfer"].values() == [accounts[0], accounts[1], amount]
