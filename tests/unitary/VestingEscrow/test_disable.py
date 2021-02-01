import brownie


def test_toggle_admin_only(vesting, accounts):
    with brownie.reverts("dev: admin only"):
        vesting.toggle_disable(accounts[2], {"from": accounts[1]})


def test_disable_can_disable_admin_only(vesting, accounts):
    with brownie.reverts("dev: admin only"):
        vesting.disable_can_disable({"from": accounts[1]})


def test_disabled_at_is_initially_zero(vesting, accounts):
    assert vesting.disabled_at(accounts[1]) == 0


def test_disable(vesting, accounts):
    tx = vesting.toggle_disable(accounts[1], {"from": accounts[0]})

    assert vesting.disabled_at(accounts[1]) == tx.timestamp


def test_disable_reenable(vesting, accounts):
    vesting.toggle_disable(accounts[1], {"from": accounts[0]})
    vesting.toggle_disable(accounts[1], {"from": accounts[0]})

    assert vesting.disabled_at(accounts[1]) == 0


def test_disable_can_disable(vesting, accounts):
    vesting.disable_can_disable({"from": accounts[0]})
    assert vesting.can_disable() is False

    with brownie.reverts("Cannot disable"):
        vesting.toggle_disable(accounts[1], {"from": accounts[0]})


def test_disable_can_disable_cannot_reenable(vesting, accounts):
    vesting.disable_can_disable({"from": accounts[0]})
    vesting.disable_can_disable({"from": accounts[0]})
    assert vesting.can_disable() is False
