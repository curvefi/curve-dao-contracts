import brownie


def test_commit_admin_only(vesting_factory, accounts):
    with brownie.reverts("dev: admin only"):
        vesting_factory.commit_transfer_ownership(accounts[1], {'from': accounts[1]})


def test_apply_admin_only(vesting_factory, accounts):
    with brownie.reverts("dev: admin only"):
        vesting_factory.apply_transfer_ownership({'from': accounts[1]})


def test_commit_transfer_ownership(vesting_factory, accounts):
    vesting_factory.commit_transfer_ownership(accounts[1], {'from': accounts[0]})

    assert vesting_factory.admin() == accounts[0]
    assert vesting_factory.future_admin() == accounts[1]


def test_apply_transfer_ownership(vesting_factory, accounts):
    vesting_factory.commit_transfer_ownership(accounts[1], {'from': accounts[0]})
    vesting_factory.apply_transfer_ownership({'from': accounts[0]})

    assert vesting_factory.admin() == accounts[1]


def test_apply_without_commit(vesting_factory, accounts):
    with brownie.reverts("dev: admin not set"):
        vesting_factory.apply_transfer_ownership({'from': accounts[0]})
