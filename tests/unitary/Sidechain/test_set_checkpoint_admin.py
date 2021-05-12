import brownie
import pytest


@pytest.mark.parametrize("idx", range(1, 6))
def test_admin_only(root_gauge, accounts, idx):
    with brownie.reverts("dev: admin only"):
        root_gauge.set_checkpoint_admin(accounts[idx], {"from": accounts[idx]})


def test_immediate_change_of_admin(alice, bob, root_gauge):
    root_gauge.set_checkpoint_admin(bob, {"from": alice})

    assert root_gauge.checkpoint_admin() == bob
