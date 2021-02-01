#!/usr/bin/python3
import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(
    accounts,
    gauge_controller,
    minter,
    liquidity_gauge_reward,
    reward_gauge_wrapper,
    token,
    mock_lp_token,
):
    token.set_minter(minter, {"from": accounts[0]})

    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": accounts[0]})
    gauge_controller.add_gauge(liquidity_gauge_reward, 0, 0, {"from": accounts[0]})

    mock_lp_token.approve(reward_gauge_wrapper, 2 ** 256 - 1, {"from": accounts[0]})
    reward_gauge_wrapper.deposit(10 ** 18, {"from": accounts[0]})


def test_sender_balance_decreases(accounts, reward_gauge_wrapper):
    sender_balance = reward_gauge_wrapper.balanceOf(accounts[0])
    amount = sender_balance // 4

    reward_gauge_wrapper.approve(accounts[1], amount, {"from": accounts[0]})
    reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert reward_gauge_wrapper.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, reward_gauge_wrapper):
    receiver_balance = reward_gauge_wrapper.balanceOf(accounts[2])
    amount = reward_gauge_wrapper.balanceOf(accounts[0]) // 4

    reward_gauge_wrapper.approve(accounts[1], amount, {"from": accounts[0]})
    reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert reward_gauge_wrapper.balanceOf(accounts[2]) == receiver_balance + amount


def test_caller_balance_not_affected(accounts, reward_gauge_wrapper):
    caller_balance = reward_gauge_wrapper.balanceOf(accounts[1])
    amount = reward_gauge_wrapper.balanceOf(accounts[0])

    reward_gauge_wrapper.approve(accounts[1], amount, {"from": accounts[0]})
    reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert reward_gauge_wrapper.balanceOf(accounts[1]) == caller_balance


def test_caller_approval_affected(accounts, reward_gauge_wrapper):
    approval_amount = reward_gauge_wrapper.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    reward_gauge_wrapper.approve(accounts[1], approval_amount, {"from": accounts[0]})
    reward_gauge_wrapper.transferFrom(
        accounts[0], accounts[2], transfer_amount, {"from": accounts[1]}
    )

    assert (
        reward_gauge_wrapper.allowance(accounts[0], accounts[1])
        == approval_amount - transfer_amount
    )


def test_receiver_approval_not_affected(accounts, reward_gauge_wrapper):
    approval_amount = reward_gauge_wrapper.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    reward_gauge_wrapper.approve(accounts[1], approval_amount, {"from": accounts[0]})
    reward_gauge_wrapper.approve(accounts[2], approval_amount, {"from": accounts[0]})
    reward_gauge_wrapper.transferFrom(
        accounts[0], accounts[2], transfer_amount, {"from": accounts[1]}
    )

    assert reward_gauge_wrapper.allowance(accounts[0], accounts[2]) == approval_amount


def test_total_supply_not_affected(accounts, reward_gauge_wrapper):
    total_supply = reward_gauge_wrapper.totalSupply()
    amount = reward_gauge_wrapper.balanceOf(accounts[0])

    reward_gauge_wrapper.approve(accounts[1], amount, {"from": accounts[0]})
    reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert reward_gauge_wrapper.totalSupply() == total_supply


def test_returns_true(accounts, reward_gauge_wrapper):
    amount = reward_gauge_wrapper.balanceOf(accounts[0])
    reward_gauge_wrapper.approve(accounts[1], amount, {"from": accounts[0]})
    tx = reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, reward_gauge_wrapper):
    amount = reward_gauge_wrapper.balanceOf(accounts[0])
    receiver_balance = reward_gauge_wrapper.balanceOf(accounts[2])

    reward_gauge_wrapper.approve(accounts[1], amount, {"from": accounts[0]})
    reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert reward_gauge_wrapper.balanceOf(accounts[0]) == 0
    assert reward_gauge_wrapper.balanceOf(accounts[2]) == receiver_balance + amount


def test_transfer_zero_tokens(accounts, reward_gauge_wrapper):
    sender_balance = reward_gauge_wrapper.balanceOf(accounts[0])
    receiver_balance = reward_gauge_wrapper.balanceOf(accounts[2])

    reward_gauge_wrapper.approve(accounts[1], sender_balance, {"from": accounts[0]})
    reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], 0, {"from": accounts[1]})

    assert reward_gauge_wrapper.balanceOf(accounts[0]) == sender_balance
    assert reward_gauge_wrapper.balanceOf(accounts[2]) == receiver_balance


def test_transfer_zero_tokens_without_approval(accounts, reward_gauge_wrapper):
    sender_balance = reward_gauge_wrapper.balanceOf(accounts[0])
    receiver_balance = reward_gauge_wrapper.balanceOf(accounts[2])

    reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], 0, {"from": accounts[1]})

    assert reward_gauge_wrapper.balanceOf(accounts[0]) == sender_balance
    assert reward_gauge_wrapper.balanceOf(accounts[2]) == receiver_balance


def test_insufficient_balance(accounts, reward_gauge_wrapper):
    balance = reward_gauge_wrapper.balanceOf(accounts[0])

    reward_gauge_wrapper.approve(accounts[1], balance + 1, {"from": accounts[0]})
    with brownie.reverts():
        reward_gauge_wrapper.transferFrom(
            accounts[0], accounts[2], balance + 1, {"from": accounts[1]}
        )


def test_insufficient_approval(accounts, reward_gauge_wrapper):
    balance = reward_gauge_wrapper.balanceOf(accounts[0])

    reward_gauge_wrapper.approve(accounts[1], balance - 1, {"from": accounts[0]})
    with brownie.reverts():
        reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], balance, {"from": accounts[1]})


def test_no_approval(accounts, reward_gauge_wrapper):
    balance = reward_gauge_wrapper.balanceOf(accounts[0])

    with brownie.reverts():
        reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], balance, {"from": accounts[1]})


def test_infinite_approval(accounts, reward_gauge_wrapper):
    reward_gauge_wrapper.approve(accounts[1], 2 ** 256 - 1, {"from": accounts[0]})
    reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], 10000, {"from": accounts[1]})

    assert reward_gauge_wrapper.allowance(accounts[0], accounts[1]) == 2 ** 256 - 1


def test_revoked_approval(accounts, reward_gauge_wrapper):
    balance = reward_gauge_wrapper.balanceOf(accounts[0])

    reward_gauge_wrapper.approve(accounts[1], balance, {"from": accounts[0]})
    reward_gauge_wrapper.approve(accounts[1], 0, {"from": accounts[0]})

    with brownie.reverts():
        reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], balance, {"from": accounts[1]})


def test_transfer_to_self(accounts, reward_gauge_wrapper):
    sender_balance = reward_gauge_wrapper.balanceOf(accounts[0])
    amount = sender_balance // 4

    reward_gauge_wrapper.approve(accounts[0], sender_balance, {"from": accounts[0]})
    reward_gauge_wrapper.transferFrom(accounts[0], accounts[0], amount, {"from": accounts[0]})

    assert reward_gauge_wrapper.balanceOf(accounts[0]) == sender_balance
    assert reward_gauge_wrapper.allowance(accounts[0], accounts[0]) == sender_balance - amount


def test_transfer_to_self_no_approval(accounts, reward_gauge_wrapper):
    amount = reward_gauge_wrapper.balanceOf(accounts[0])

    with brownie.reverts():
        reward_gauge_wrapper.transferFrom(accounts[0], accounts[0], amount, {"from": accounts[0]})


def test_transfer_event_fires(accounts, reward_gauge_wrapper):
    amount = reward_gauge_wrapper.balanceOf(accounts[0])

    reward_gauge_wrapper.approve(accounts[1], amount, {"from": accounts[0]})
    tx = reward_gauge_wrapper.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert tx.events["Transfer"][-1].values() == [accounts[0], accounts[2], amount]
