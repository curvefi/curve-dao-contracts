import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_toggle_admin_only(vesting_simple, accounts):
    with brownie.reverts():
        vesting_simple.toggle_disable(accounts[2], {"from": accounts[1]})


def test_disable_can_disable_admin_only(vesting_simple, accounts):
    with brownie.reverts():
        vesting_simple.disable_can_disable({"from": accounts[1]})


def test_disabled_at_is_initially_zero(vesting_simple, accounts):
    assert vesting_simple.disabled_at(accounts[1]) == 0


def test_disable(vesting_simple, accounts):
    tx = vesting_simple.toggle_disable(accounts[1], {"from": accounts[0]})

    assert vesting_simple.disabled_at(accounts[1]) == tx.timestamp


def test_disable_reenable(vesting_simple, accounts):
    vesting_simple.toggle_disable(accounts[1], {"from": accounts[0]})
    vesting_simple.toggle_disable(accounts[1], {"from": accounts[0]})

    assert vesting_simple.disabled_at(accounts[1]) == 0


def test_disable_can_disable(vesting_simple, accounts):
    vesting_simple.disable_can_disable({"from": accounts[0]})
    assert vesting_simple.can_disable() is False

    with brownie.reverts():
        vesting_simple.toggle_disable(accounts[1], {"from": accounts[0]})


def test_disable_can_disable_cannot_reenable(vesting_simple, accounts):
    vesting_simple.disable_can_disable({"from": accounts[0]})
    vesting_simple.disable_can_disable({"from": accounts[0]})
    assert vesting_simple.can_disable() is False
