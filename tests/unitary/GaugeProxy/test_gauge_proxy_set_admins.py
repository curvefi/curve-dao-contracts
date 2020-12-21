import brownie
import pytest
from brownie import ZERO_ADDRESS


def test_assumptions(gauge_proxy, alice, bob):
    assert gauge_proxy.ownership_admin() == alice
    assert gauge_proxy.emergency_admin() == bob

    assert gauge_proxy.future_ownership_admin() == ZERO_ADDRESS
    assert gauge_proxy.future_emergency_admin() == ZERO_ADDRESS


def test_commit_set_admin(gauge_proxy, alice, bob, charlie):
    gauge_proxy.commit_set_admins(bob, charlie, {'from': alice})

    assert gauge_proxy.ownership_admin() == alice
    assert gauge_proxy.emergency_admin() == bob

    assert gauge_proxy.future_ownership_admin() == bob
    assert gauge_proxy.future_emergency_admin() == charlie


def test_accept_set_admin(gauge_proxy, alice, bob, charlie):
    gauge_proxy.commit_set_admins(bob, charlie, {'from': alice})
    gauge_proxy.accept_set_admins({'from': bob})

    assert gauge_proxy.ownership_admin() == bob
    assert gauge_proxy.emergency_admin() == charlie

    assert gauge_proxy.future_ownership_admin() == bob
    assert gauge_proxy.future_emergency_admin() == charlie


@pytest.mark.parametrize('idx', range(1, 4))
def test_commit_only_owner(accounts, alice, gauge_proxy, idx):
    with brownie.reverts("Access denied"):
        gauge_proxy.commit_set_admins(alice, alice, {'from': accounts[idx]})


@pytest.mark.parametrize('idx', range(1, 4))
def test_accept_only_owner(accounts, alice, bob, gauge_proxy, idx):
    gauge_proxy.commit_set_admins(alice, bob, {'from': alice})

    with brownie.reverts("Access denied"):
        gauge_proxy.accept_set_admins({'from': accounts[idx]})
