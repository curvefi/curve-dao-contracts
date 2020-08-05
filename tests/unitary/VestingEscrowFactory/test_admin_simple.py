import brownie


def test_commit_admin_only(vesting_simple, accounts):
    with brownie.reverts("dev: admin only"):
        vesting_simple.commit_transfer_ownership(accounts[1], {'from': accounts[1]})


def test_apply_admin_only(vesting_simple, accounts):
    with brownie.reverts("dev: admin only"):
        vesting_simple.apply_transfer_ownership({'from': accounts[1]})


def test_commit_transfer_ownership(vesting_simple, accounts):
    vesting_simple.commit_transfer_ownership(accounts[1], {'from': accounts[0]})

    assert vesting_simple.admin() == accounts[0]
    assert vesting_simple.future_admin() == accounts[1]


def test_apply_transfer_ownership(vesting_simple, accounts):
    vesting_simple.commit_transfer_ownership(accounts[1], {'from': accounts[0]})
    vesting_simple.apply_transfer_ownership({'from': accounts[0]})

    assert vesting_simple.admin() == accounts[1]


def test_apply_without_commit(vesting_simple, accounts):
    with brownie.reverts("dev: admin not set"):
        vesting_simple.apply_transfer_ownership({'from': accounts[0]})
