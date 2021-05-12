import brownie
import pytest


@pytest.mark.parametrize("idx", range(1, 6))
def test_admin_only(root_gauge, accounts, idx):
    with brownie.reverts("dev: admin only"):
        root_gauge.set_killed(True, {"from": accounts[idx]})


def test_set_killed_updates_state(alice, root_gauge):
    root_gauge.set_killed(True, {"from": alice})

    assert root_gauge.is_killed() is True
