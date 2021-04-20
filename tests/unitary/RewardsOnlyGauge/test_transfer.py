#!/usr/bin/python3
import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(accounts, gauge_controller, minter, rewards_only_gauge, token, mock_lp_token):
    token.set_minter(minter, {"from": accounts[0]})

    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": accounts[0]})
    gauge_controller.add_gauge(rewards_only_gauge, 0, 0, {"from": accounts[0]})

    mock_lp_token.approve(rewards_only_gauge, 2 ** 256 - 1, {"from": accounts[0]})
    rewards_only_gauge.deposit(10 ** 18, {"from": accounts[0]})


def test_sender_balance_decreases(accounts, rewards_only_gauge):
    sender_balance = rewards_only_gauge.balanceOf(accounts[0])
    amount = sender_balance // 4

    rewards_only_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert rewards_only_gauge.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, rewards_only_gauge):
    receiver_balance = rewards_only_gauge.balanceOf(accounts[1])
    amount = rewards_only_gauge.balanceOf(accounts[0]) // 4

    rewards_only_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert rewards_only_gauge.balanceOf(accounts[1]) == receiver_balance + amount


def test_total_supply_not_affected(accounts, rewards_only_gauge):
    total_supply = rewards_only_gauge.totalSupply()
    amount = rewards_only_gauge.balanceOf(accounts[0])

    rewards_only_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert rewards_only_gauge.totalSupply() == total_supply


def test_returns_true(accounts, rewards_only_gauge):
    amount = rewards_only_gauge.balanceOf(accounts[0])
    tx = rewards_only_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, rewards_only_gauge):
    amount = rewards_only_gauge.balanceOf(accounts[0])
    receiver_balance = rewards_only_gauge.balanceOf(accounts[1])

    rewards_only_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert rewards_only_gauge.balanceOf(accounts[0]) == 0
    assert rewards_only_gauge.balanceOf(accounts[1]) == receiver_balance + amount


def test_transfer_zero_tokens(accounts, rewards_only_gauge):
    sender_balance = rewards_only_gauge.balanceOf(accounts[0])
    receiver_balance = rewards_only_gauge.balanceOf(accounts[1])

    rewards_only_gauge.transfer(accounts[1], 0, {"from": accounts[0]})

    assert rewards_only_gauge.balanceOf(accounts[0]) == sender_balance
    assert rewards_only_gauge.balanceOf(accounts[1]) == receiver_balance


def test_transfer_to_self(accounts, rewards_only_gauge):
    sender_balance = rewards_only_gauge.balanceOf(accounts[0])
    amount = sender_balance // 4

    rewards_only_gauge.transfer(accounts[0], amount, {"from": accounts[0]})

    assert rewards_only_gauge.balanceOf(accounts[0]) == sender_balance


def test_insufficient_balance(accounts, rewards_only_gauge):
    balance = rewards_only_gauge.balanceOf(accounts[0])

    with brownie.reverts():
        rewards_only_gauge.transfer(accounts[1], balance + 1, {"from": accounts[0]})


def test_transfer_event_fires(accounts, rewards_only_gauge):
    amount = rewards_only_gauge.balanceOf(accounts[0])
    tx = rewards_only_gauge.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.events["Transfer"].values() == [accounts[0], accounts[1], amount]
