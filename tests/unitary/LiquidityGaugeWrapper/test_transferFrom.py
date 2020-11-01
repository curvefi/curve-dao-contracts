#!/usr/bin/python3
import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(accounts, gauge_controller, minter, liquidity_gauge, gauge_wrapper, token, mock_lp_token):
    token.set_minter(minter, {'from': accounts[0]})

    gauge_controller.add_type(b'Liquidity', 10**10, {'from': accounts[0]})
    gauge_controller.add_gauge(liquidity_gauge, 0, 0, {'from': accounts[0]})

    mock_lp_token.approve(gauge_wrapper, 2 ** 256 - 1, {"from": accounts[0]})
    gauge_wrapper.deposit(10**18, {'from': accounts[0]})


def test_sender_balance_decreases(accounts, gauge_wrapper):
    sender_balance = gauge_wrapper.balanceOf(accounts[0])
    amount = sender_balance // 4

    gauge_wrapper.approve(accounts[1], amount, {'from': accounts[0]})
    gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert gauge_wrapper.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, gauge_wrapper):
    receiver_balance = gauge_wrapper.balanceOf(accounts[2])
    amount = gauge_wrapper.balanceOf(accounts[0]) // 4

    gauge_wrapper.approve(accounts[1], amount, {'from': accounts[0]})
    gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert gauge_wrapper.balanceOf(accounts[2]) == receiver_balance + amount


def test_caller_balance_not_affected(accounts, gauge_wrapper):
    caller_balance = gauge_wrapper.balanceOf(accounts[1])
    amount = gauge_wrapper.balanceOf(accounts[0])

    gauge_wrapper.approve(accounts[1], amount, {'from': accounts[0]})
    gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert gauge_wrapper.balanceOf(accounts[1]) == caller_balance


def test_caller_approval_affected(accounts, gauge_wrapper):
    approval_amount = gauge_wrapper.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    gauge_wrapper.approve(accounts[1], approval_amount, {'from': accounts[0]})
    gauge_wrapper.transferFrom(accounts[0], accounts[2], transfer_amount, {'from': accounts[1]})

    assert gauge_wrapper.allowance(accounts[0], accounts[1]) == approval_amount - transfer_amount


def test_receiver_approval_not_affected(accounts, gauge_wrapper):
    approval_amount = gauge_wrapper.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    gauge_wrapper.approve(accounts[1], approval_amount, {'from': accounts[0]})
    gauge_wrapper.approve(accounts[2], approval_amount, {'from': accounts[0]})
    gauge_wrapper.transferFrom(accounts[0], accounts[2], transfer_amount, {'from': accounts[1]})

    assert gauge_wrapper.allowance(accounts[0], accounts[2]) == approval_amount


def test_total_supply_not_affected(accounts, gauge_wrapper):
    total_supply = gauge_wrapper.totalSupply()
    amount = gauge_wrapper.balanceOf(accounts[0])

    gauge_wrapper.approve(accounts[1], amount, {'from': accounts[0]})
    gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert gauge_wrapper.totalSupply() == total_supply


def test_returns_true(accounts, gauge_wrapper):
    amount = gauge_wrapper.balanceOf(accounts[0])
    gauge_wrapper.approve(accounts[1], amount, {'from': accounts[0]})
    tx = gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, gauge_wrapper):
    amount = gauge_wrapper.balanceOf(accounts[0])
    receiver_balance = gauge_wrapper.balanceOf(accounts[2])

    gauge_wrapper.approve(accounts[1], amount, {'from': accounts[0]})
    gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert gauge_wrapper.balanceOf(accounts[0]) == 0
    assert gauge_wrapper.balanceOf(accounts[2]) == receiver_balance + amount


def test_transfer_zero_tokens(accounts, gauge_wrapper):
    sender_balance = gauge_wrapper.balanceOf(accounts[0])
    receiver_balance = gauge_wrapper.balanceOf(accounts[2])

    gauge_wrapper.approve(accounts[1], sender_balance, {'from': accounts[0]})
    gauge_wrapper.transferFrom(accounts[0], accounts[2], 0, {'from': accounts[1]})

    assert gauge_wrapper.balanceOf(accounts[0]) == sender_balance
    assert gauge_wrapper.balanceOf(accounts[2]) == receiver_balance


def test_transfer_zero_tokens_without_approval(accounts, gauge_wrapper):
    sender_balance = gauge_wrapper.balanceOf(accounts[0])
    receiver_balance = gauge_wrapper.balanceOf(accounts[2])

    gauge_wrapper.transferFrom(accounts[0], accounts[2], 0, {'from': accounts[1]})

    assert gauge_wrapper.balanceOf(accounts[0]) == sender_balance
    assert gauge_wrapper.balanceOf(accounts[2]) == receiver_balance


def test_insufficient_balance(accounts, gauge_wrapper):
    balance = gauge_wrapper.balanceOf(accounts[0])

    gauge_wrapper.approve(accounts[1], balance + 1, {'from': accounts[0]})
    with brownie.reverts():
        gauge_wrapper.transferFrom(accounts[0], accounts[2], balance + 1, {'from': accounts[1]})


def test_insufficient_approval(accounts, gauge_wrapper):
    balance = gauge_wrapper.balanceOf(accounts[0])

    gauge_wrapper.approve(accounts[1], balance - 1, {'from': accounts[0]})
    with brownie.reverts():
        gauge_wrapper.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_no_approval(accounts, gauge_wrapper):
    balance = gauge_wrapper.balanceOf(accounts[0])

    with brownie.reverts():
        gauge_wrapper.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_infinite_approval(accounts, gauge_wrapper):
    gauge_wrapper.approve(accounts[1], 2**256-1, {'from': accounts[0]})
    gauge_wrapper.transferFrom(accounts[0], accounts[2], 10000, {'from': accounts[1]})

    assert gauge_wrapper.allowance(accounts[0], accounts[1]) == 2**256-1


def test_revoked_approval(accounts, gauge_wrapper):
    balance = gauge_wrapper.balanceOf(accounts[0])

    gauge_wrapper.approve(accounts[1], balance, {'from': accounts[0]})
    gauge_wrapper.approve(accounts[1], 0, {'from': accounts[0]})

    with brownie.reverts():
        gauge_wrapper.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_transfer_to_self(accounts, gauge_wrapper):
    sender_balance = gauge_wrapper.balanceOf(accounts[0])
    amount = sender_balance // 4

    gauge_wrapper.approve(accounts[0], sender_balance, {'from': accounts[0]})
    gauge_wrapper.transferFrom(accounts[0], accounts[0], amount, {'from': accounts[0]})

    assert gauge_wrapper.balanceOf(accounts[0]) == sender_balance
    assert gauge_wrapper.allowance(accounts[0], accounts[0]) == sender_balance - amount


def test_transfer_to_self_no_approval(accounts, gauge_wrapper):
    amount = gauge_wrapper.balanceOf(accounts[0])

    with brownie.reverts():
        gauge_wrapper.transferFrom(accounts[0], accounts[0], amount, {'from': accounts[0]})


def test_transfer_event_fires(accounts, gauge_wrapper):
    amount = gauge_wrapper.balanceOf(accounts[0])

    gauge_wrapper.approve(accounts[1], amount, {'from': accounts[0]})
    tx = gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert tx.events["Transfer"].values() == [accounts[0], accounts[2], amount]
