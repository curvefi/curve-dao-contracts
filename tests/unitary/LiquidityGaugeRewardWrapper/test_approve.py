#!/usr/bin/python3

import pytest


@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(reward_gauge_wrapper, accounts, idx):
    assert reward_gauge_wrapper.allowance(accounts[0], accounts[idx]) == 0


def test_approve(reward_gauge_wrapper, accounts):
    reward_gauge_wrapper.approve(accounts[1], 10 ** 19, {"from": accounts[0]})

    assert reward_gauge_wrapper.allowance(accounts[0], accounts[1]) == 10 ** 19


def test_modify_approve(reward_gauge_wrapper, accounts):
    reward_gauge_wrapper.approve(accounts[1], 10 ** 19, {"from": accounts[0]})
    reward_gauge_wrapper.approve(accounts[1], 12345678, {"from": accounts[0]})

    assert reward_gauge_wrapper.allowance(accounts[0], accounts[1]) == 12345678


def test_revoke_approve(reward_gauge_wrapper, accounts):
    reward_gauge_wrapper.approve(accounts[1], 10 ** 19, {"from": accounts[0]})
    reward_gauge_wrapper.approve(accounts[1], 0, {"from": accounts[0]})

    assert reward_gauge_wrapper.allowance(accounts[0], accounts[1]) == 0


def test_approve_self(reward_gauge_wrapper, accounts):
    reward_gauge_wrapper.approve(accounts[0], 10 ** 19, {"from": accounts[0]})

    assert reward_gauge_wrapper.allowance(accounts[0], accounts[0]) == 10 ** 19


def test_only_affects_target(reward_gauge_wrapper, accounts):
    reward_gauge_wrapper.approve(accounts[1], 10 ** 19, {"from": accounts[0]})

    assert reward_gauge_wrapper.allowance(accounts[1], accounts[0]) == 0


def test_returns_true(reward_gauge_wrapper, accounts):
    tx = reward_gauge_wrapper.approve(accounts[1], 10 ** 19, {"from": accounts[0]})

    assert tx.return_value is True


def test_approval_event_fires(accounts, reward_gauge_wrapper):
    tx = reward_gauge_wrapper.approve(accounts[1], 10 ** 19, {"from": accounts[0]})

    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [accounts[0], accounts[1], 10 ** 19]


def test_increase_allowance(accounts, reward_gauge_wrapper):
    reward_gauge_wrapper.approve(accounts[1], 100, {"from": accounts[0]})
    reward_gauge_wrapper.increaseAllowance(accounts[1], 403, {"from": accounts[0]})

    assert reward_gauge_wrapper.allowance(accounts[0], accounts[1]) == 503


def test_decrease_allowance(accounts, reward_gauge_wrapper):
    reward_gauge_wrapper.approve(accounts[1], 100, {"from": accounts[0]})
    reward_gauge_wrapper.decreaseAllowance(accounts[1], 34, {"from": accounts[0]})

    assert reward_gauge_wrapper.allowance(accounts[0], accounts[1]) == 66
