import pytest


@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(gauge_v3, accounts, idx):
    assert gauge_v3.allowance(accounts[0], accounts[idx]) == 0


def test_approve(gauge_v3, accounts):
    gauge_v3.approve(accounts[1], 10 ** 19, {"from": accounts[0]})

    assert gauge_v3.allowance(accounts[0], accounts[1]) == 10 ** 19


def test_modify_approve(gauge_v3, accounts):
    gauge_v3.approve(accounts[1], 10 ** 19, {"from": accounts[0]})
    gauge_v3.approve(accounts[1], 12345678, {"from": accounts[0]})

    assert gauge_v3.allowance(accounts[0], accounts[1]) == 12345678


def test_revoke_approve(gauge_v3, accounts):
    gauge_v3.approve(accounts[1], 10 ** 19, {"from": accounts[0]})
    gauge_v3.approve(accounts[1], 0, {"from": accounts[0]})

    assert gauge_v3.allowance(accounts[0], accounts[1]) == 0


def test_approve_self(gauge_v3, accounts):
    gauge_v3.approve(accounts[0], 10 ** 19, {"from": accounts[0]})

    assert gauge_v3.allowance(accounts[0], accounts[0]) == 10 ** 19


def test_only_affects_target(gauge_v3, accounts):
    gauge_v3.approve(accounts[1], 10 ** 19, {"from": accounts[0]})

    assert gauge_v3.allowance(accounts[1], accounts[0]) == 0


def test_returns_true(gauge_v3, accounts):
    tx = gauge_v3.approve(accounts[1], 10 ** 19, {"from": accounts[0]})

    assert tx.return_value is True


def test_approval_event_fires(accounts, gauge_v3):
    tx = gauge_v3.approve(accounts[1], 10 ** 19, {"from": accounts[0]})

    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [accounts[0], accounts[1], 10 ** 19]


def test_increase_allowance(accounts, gauge_v3):
    gauge_v3.approve(accounts[1], 100, {"from": accounts[0]})
    gauge_v3.increaseAllowance(accounts[1], 403, {"from": accounts[0]})

    assert gauge_v3.allowance(accounts[0], accounts[1]) == 503


def test_decrease_allowance(accounts, gauge_v3):
    gauge_v3.approve(accounts[1], 100, {"from": accounts[0]})
    gauge_v3.decreaseAllowance(accounts[1], 34, {"from": accounts[0]})

    assert gauge_v3.allowance(accounts[0], accounts[1]) == 66
