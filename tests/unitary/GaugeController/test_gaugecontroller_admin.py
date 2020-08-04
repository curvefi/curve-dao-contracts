import brownie


def test_commit_admin_only(gauge_controller, accounts):
    with brownie.reverts("dev: admin only"):
        gauge_controller.commit_transfer_ownership(accounts[1], {'from': accounts[1]})


def test_apply_admin_only(gauge_controller, accounts):
    with brownie.reverts("dev: admin only"):
        gauge_controller.apply_transfer_ownership({'from': accounts[1]})


def test_commit_transfer_ownership(gauge_controller, accounts):
    gauge_controller.commit_transfer_ownership(accounts[1], {'from': accounts[0]})

    assert gauge_controller.admin() == accounts[0]
    assert gauge_controller.future_admin() == accounts[1]


def test_apply_transfer_ownership(gauge_controller, accounts):
    gauge_controller.commit_transfer_ownership(accounts[1], {'from': accounts[0]})
    gauge_controller.apply_transfer_ownership({'from': accounts[0]})

    assert gauge_controller.admin() == accounts[1]


def test_apply_without_commit(gauge_controller, accounts):
    with brownie.reverts("dev: admin not set"):
        gauge_controller.apply_transfer_ownership({'from': accounts[0]})
