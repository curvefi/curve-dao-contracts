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

    rewards_only_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    rewards_only_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert rewards_only_gauge.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, rewards_only_gauge):
    receiver_balance = rewards_only_gauge.balanceOf(accounts[2])
    amount = rewards_only_gauge.balanceOf(accounts[0]) // 4

    rewards_only_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    rewards_only_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert rewards_only_gauge.balanceOf(accounts[2]) == receiver_balance + amount


def test_caller_balance_not_affected(accounts, rewards_only_gauge):
    caller_balance = rewards_only_gauge.balanceOf(accounts[1])
    amount = rewards_only_gauge.balanceOf(accounts[0])

    rewards_only_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    rewards_only_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert rewards_only_gauge.balanceOf(accounts[1]) == caller_balance


def test_caller_approval_affected(accounts, rewards_only_gauge):
    approval_amount = rewards_only_gauge.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    rewards_only_gauge.approve(accounts[1], approval_amount, {"from": accounts[0]})
    rewards_only_gauge.transferFrom(
        accounts[0], accounts[2], transfer_amount, {"from": accounts[1]}
    )

    assert (
        rewards_only_gauge.allowance(accounts[0], accounts[1]) == approval_amount - transfer_amount
    )


def test_receiver_approval_not_affected(accounts, rewards_only_gauge):
    approval_amount = rewards_only_gauge.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    rewards_only_gauge.approve(accounts[1], approval_amount, {"from": accounts[0]})
    rewards_only_gauge.approve(accounts[2], approval_amount, {"from": accounts[0]})
    rewards_only_gauge.transferFrom(
        accounts[0], accounts[2], transfer_amount, {"from": accounts[1]}
    )

    assert rewards_only_gauge.allowance(accounts[0], accounts[2]) == approval_amount


def test_total_supply_not_affected(accounts, rewards_only_gauge):
    total_supply = rewards_only_gauge.totalSupply()
    amount = rewards_only_gauge.balanceOf(accounts[0])

    rewards_only_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    rewards_only_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert rewards_only_gauge.totalSupply() == total_supply


def test_returns_true(accounts, rewards_only_gauge):
    amount = rewards_only_gauge.balanceOf(accounts[0])
    rewards_only_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    tx = rewards_only_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, rewards_only_gauge):
    amount = rewards_only_gauge.balanceOf(accounts[0])
    receiver_balance = rewards_only_gauge.balanceOf(accounts[2])

    rewards_only_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    rewards_only_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert rewards_only_gauge.balanceOf(accounts[0]) == 0
    assert rewards_only_gauge.balanceOf(accounts[2]) == receiver_balance + amount


def test_transfer_zero_tokens(accounts, rewards_only_gauge):
    sender_balance = rewards_only_gauge.balanceOf(accounts[0])
    receiver_balance = rewards_only_gauge.balanceOf(accounts[2])

    rewards_only_gauge.approve(accounts[1], sender_balance, {"from": accounts[0]})
    rewards_only_gauge.transferFrom(accounts[0], accounts[2], 0, {"from": accounts[1]})

    assert rewards_only_gauge.balanceOf(accounts[0]) == sender_balance
    assert rewards_only_gauge.balanceOf(accounts[2]) == receiver_balance


def test_transfer_zero_tokens_without_approval(accounts, rewards_only_gauge):
    sender_balance = rewards_only_gauge.balanceOf(accounts[0])
    receiver_balance = rewards_only_gauge.balanceOf(accounts[2])

    rewards_only_gauge.transferFrom(accounts[0], accounts[2], 0, {"from": accounts[1]})

    assert rewards_only_gauge.balanceOf(accounts[0]) == sender_balance
    assert rewards_only_gauge.balanceOf(accounts[2]) == receiver_balance


def test_insufficient_balance(accounts, rewards_only_gauge):
    balance = rewards_only_gauge.balanceOf(accounts[0])

    rewards_only_gauge.approve(accounts[1], balance + 1, {"from": accounts[0]})
    with brownie.reverts():
        rewards_only_gauge.transferFrom(
            accounts[0], accounts[2], balance + 1, {"from": accounts[1]}
        )


def test_insufficient_approval(accounts, rewards_only_gauge):
    balance = rewards_only_gauge.balanceOf(accounts[0])

    rewards_only_gauge.approve(accounts[1], balance - 1, {"from": accounts[0]})
    with brownie.reverts():
        rewards_only_gauge.transferFrom(accounts[0], accounts[2], balance, {"from": accounts[1]})


def test_no_approval(accounts, rewards_only_gauge):
    balance = rewards_only_gauge.balanceOf(accounts[0])

    with brownie.reverts():
        rewards_only_gauge.transferFrom(accounts[0], accounts[2], balance, {"from": accounts[1]})


def test_infinite_approval(accounts, rewards_only_gauge):
    rewards_only_gauge.approve(accounts[1], 2 ** 256 - 1, {"from": accounts[0]})
    rewards_only_gauge.transferFrom(accounts[0], accounts[2], 10000, {"from": accounts[1]})

    assert rewards_only_gauge.allowance(accounts[0], accounts[1]) == 2 ** 256 - 1


def test_revoked_approval(accounts, rewards_only_gauge):
    balance = rewards_only_gauge.balanceOf(accounts[0])

    rewards_only_gauge.approve(accounts[1], balance, {"from": accounts[0]})
    rewards_only_gauge.approve(accounts[1], 0, {"from": accounts[0]})

    with brownie.reverts():
        rewards_only_gauge.transferFrom(accounts[0], accounts[2], balance, {"from": accounts[1]})


def test_transfer_to_self(accounts, rewards_only_gauge):
    sender_balance = rewards_only_gauge.balanceOf(accounts[0])
    amount = sender_balance // 4

    rewards_only_gauge.approve(accounts[0], sender_balance, {"from": accounts[0]})
    rewards_only_gauge.transferFrom(accounts[0], accounts[0], amount, {"from": accounts[0]})

    assert rewards_only_gauge.balanceOf(accounts[0]) == sender_balance
    assert rewards_only_gauge.allowance(accounts[0], accounts[0]) == sender_balance - amount


def test_transfer_to_self_no_approval(accounts, rewards_only_gauge):
    amount = rewards_only_gauge.balanceOf(accounts[0])

    with brownie.reverts():
        rewards_only_gauge.transferFrom(accounts[0], accounts[0], amount, {"from": accounts[0]})


def test_transfer_event_fires(accounts, rewards_only_gauge):
    amount = rewards_only_gauge.balanceOf(accounts[0])

    rewards_only_gauge.approve(accounts[1], amount, {"from": accounts[0]})
    tx = rewards_only_gauge.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert tx.events["Transfer"].values() == [accounts[0], accounts[2], amount]
