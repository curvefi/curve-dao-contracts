import brownie


def test_commit_admin_only(vesting, accounts):
    with brownie.reverts("dev: admin only"):
        vesting.commit_transfer_ownership(accounts[1], {'from': accounts[1]})


def test_apply_admin_only(vesting, accounts):
    with brownie.reverts("dev: admin only"):
        vesting.apply_transfer_ownership({'from': accounts[1]})


def test_commit_transfer_ownership(vesting, accounts):
    vesting.commit_transfer_ownership(accounts[1], {'from': accounts[0]})

    assert vesting.admin() == accounts[0]
    assert vesting.future_admin() == accounts[1]


def test_apply_transfer_ownership(vesting, accounts):
    vesting.commit_transfer_ownership(accounts[1], {'from': accounts[0]})
    vesting.apply_transfer_ownership({'from': accounts[0]})

    assert vesting.admin() == accounts[1]


def test_apply_without_commit(vesting, accounts):
    with brownie.reverts("dev: admin not set"):
        vesting.apply_transfer_ownership({'from': accounts[0]})
