import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def local_setup(alice, bob, root_gauge):
    root_gauge.commit_transfer_ownership(bob, {"from": alice})


@pytest.mark.parametrize("idx", range(2, 6))
def test_future_admin_only(root_gauge, accounts, idx):
    with brownie.reverts("dev: future admin only"):
        root_gauge.accept_transfer_ownership({"from": accounts[idx]})


def test_admin_updated(root_gauge, bob):
    before = root_gauge.admin()
    root_gauge.accept_transfer_ownership({"from": bob})

    assert before != bob
    assert root_gauge.admin() == bob


def test_event_emitted(bob, root_gauge):
    tx = root_gauge.accept_transfer_ownership({"from": bob})

    assert "ApplyOwnership" in tx.events
    assert tx.events["ApplyOwnership"]["admin"] == bob
