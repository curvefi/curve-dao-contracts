#!/usr/bin/python3
import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(
    accounts, gauge_controller, minter, liquidity_gauge, gauge_wrapper, token, mock_lp_token,
):
    token.set_minter(minter, {"from": accounts[0]})

    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": accounts[0]})
    gauge_controller.add_gauge(liquidity_gauge, 0, 0, {"from": accounts[0]})

    mock_lp_token.approve(gauge_wrapper, 2 ** 256 - 1, {"from": accounts[0]})
    gauge_wrapper.deposit(10 ** 18, {"from": accounts[0]})


def test_sender_balance_decreases(accounts, gauge_wrapper):
    sender_balance = gauge_wrapper.balanceOf(accounts[0])
    amount = sender_balance // 4

    gauge_wrapper.transfer(accounts[1], amount, {"from": accounts[0]})

    assert gauge_wrapper.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, gauge_wrapper):
    receiver_balance = gauge_wrapper.balanceOf(accounts[1])
    amount = gauge_wrapper.balanceOf(accounts[0]) // 4

    gauge_wrapper.transfer(accounts[1], amount, {"from": accounts[0]})

    assert gauge_wrapper.balanceOf(accounts[1]) == receiver_balance + amount


def test_total_supply_not_affected(accounts, gauge_wrapper):
    total_supply = gauge_wrapper.totalSupply()
    amount = gauge_wrapper.balanceOf(accounts[0])

    gauge_wrapper.transfer(accounts[1], amount, {"from": accounts[0]})

    assert gauge_wrapper.totalSupply() == total_supply


def test_returns_true(accounts, gauge_wrapper):
    amount = gauge_wrapper.balanceOf(accounts[0])
    tx = gauge_wrapper.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, gauge_wrapper):
    amount = gauge_wrapper.balanceOf(accounts[0])
    receiver_balance = gauge_wrapper.balanceOf(accounts[1])

    gauge_wrapper.transfer(accounts[1], amount, {"from": accounts[0]})

    assert gauge_wrapper.balanceOf(accounts[0]) == 0
    assert gauge_wrapper.balanceOf(accounts[1]) == receiver_balance + amount


def test_transfer_zero_tokens(accounts, gauge_wrapper):
    sender_balance = gauge_wrapper.balanceOf(accounts[0])
    receiver_balance = gauge_wrapper.balanceOf(accounts[1])

    gauge_wrapper.transfer(accounts[1], 0, {"from": accounts[0]})

    assert gauge_wrapper.balanceOf(accounts[0]) == sender_balance
    assert gauge_wrapper.balanceOf(accounts[1]) == receiver_balance


def test_transfer_to_self(accounts, gauge_wrapper):
    sender_balance = gauge_wrapper.balanceOf(accounts[0])
    amount = sender_balance // 4

    gauge_wrapper.transfer(accounts[0], amount, {"from": accounts[0]})

    assert gauge_wrapper.balanceOf(accounts[0]) == sender_balance


def test_insufficient_balance(accounts, gauge_wrapper):
    balance = gauge_wrapper.balanceOf(accounts[0])

    with brownie.reverts():
        gauge_wrapper.transfer(accounts[1], balance + 1, {"from": accounts[0]})


def test_transfer_event_fires(accounts, gauge_wrapper):
    amount = gauge_wrapper.balanceOf(accounts[0])
    tx = gauge_wrapper.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.events["Transfer"].values() == [accounts[0], accounts[1], amount]
