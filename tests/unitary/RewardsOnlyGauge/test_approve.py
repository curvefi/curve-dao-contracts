import pytest


@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(rewards_only_gauge, accounts, idx):
    assert rewards_only_gauge.allowance(accounts[0], accounts[idx]) == 0


def test_approve(rewards_only_gauge, accounts):
    rewards_only_gauge.approve(accounts[1], 10 ** 19, {"from": accounts[0]})

    assert rewards_only_gauge.allowance(accounts[0], accounts[1]) == 10 ** 19


def test_modify_approve(rewards_only_gauge, accounts):
    rewards_only_gauge.approve(accounts[1], 10 ** 19, {"from": accounts[0]})
    rewards_only_gauge.approve(accounts[1], 12345678, {"from": accounts[0]})

    assert rewards_only_gauge.allowance(accounts[0], accounts[1]) == 12345678


def test_revoke_approve(rewards_only_gauge, accounts):
    rewards_only_gauge.approve(accounts[1], 10 ** 19, {"from": accounts[0]})
    rewards_only_gauge.approve(accounts[1], 0, {"from": accounts[0]})

    assert rewards_only_gauge.allowance(accounts[0], accounts[1]) == 0


def test_approve_self(rewards_only_gauge, accounts):
    rewards_only_gauge.approve(accounts[0], 10 ** 19, {"from": accounts[0]})

    assert rewards_only_gauge.allowance(accounts[0], accounts[0]) == 10 ** 19


def test_only_affects_target(rewards_only_gauge, accounts):
    rewards_only_gauge.approve(accounts[1], 10 ** 19, {"from": accounts[0]})

    assert rewards_only_gauge.allowance(accounts[1], accounts[0]) == 0


def test_returns_true(rewards_only_gauge, accounts):
    tx = rewards_only_gauge.approve(accounts[1], 10 ** 19, {"from": accounts[0]})

    assert tx.return_value is True


def test_approval_event_fires(accounts, rewards_only_gauge):
    tx = rewards_only_gauge.approve(accounts[1], 10 ** 19, {"from": accounts[0]})

    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [accounts[0], accounts[1], 10 ** 19]


def test_increase_allowance(accounts, rewards_only_gauge):
    rewards_only_gauge.approve(accounts[1], 100, {"from": accounts[0]})
    rewards_only_gauge.increaseAllowance(accounts[1], 403, {"from": accounts[0]})

    assert rewards_only_gauge.allowance(accounts[0], accounts[1]) == 503


def test_decrease_allowance(accounts, rewards_only_gauge):
    rewards_only_gauge.approve(accounts[1], 100, {"from": accounts[0]})
    rewards_only_gauge.decreaseAllowance(accounts[1], 34, {"from": accounts[0]})

    assert rewards_only_gauge.allowance(accounts[0], accounts[1]) == 66
