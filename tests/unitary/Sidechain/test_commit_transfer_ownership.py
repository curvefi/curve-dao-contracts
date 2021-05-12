import brownie
import pytest


@pytest.mark.parametrize("idx", range(1, 6))
def test_admin_only(root_gauge, accounts, idx):
    with brownie.reverts("dev: admin only"):
        root_gauge.commit_transfer_ownership(accounts[idx], {"from": accounts[idx]})


def test_admin_remains_the_same_future_admin_changed(alice, bob, root_gauge):
    before = root_gauge.future_admin()
    root_gauge.commit_transfer_ownership(bob, {"from": alice})

    assert root_gauge.admin() == alice
    assert root_gauge.future_admin() == bob and before != bob


def test_future_admin_not_admin_until_accepted(alice, bob, charlie, root_gauge):
    root_gauge.commit_transfer_ownership(bob, {"from": alice})

    with brownie.reverts("dev: admin only"):
        root_gauge.commit_transfer_ownership(charlie, {"from": bob})


def test_event_emitted(alice, bob, root_gauge):
    tx = root_gauge.commit_transfer_ownership(bob, {"from": alice})

    assert "CommitOwnership" in tx.events
    assert tx.events["CommitOwnership"]["admin"] == bob
