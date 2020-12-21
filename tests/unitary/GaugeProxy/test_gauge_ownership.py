import brownie
import pytest


@pytest.mark.parametrize('idx', range(4))
def test_accept_transfer_ownership(alice, accounts, gauge_proxy, gauge_v2, idx):
    # parametrized becuase anyone should be able to call to accept
    gauge_v2.commit_transfer_ownership(gauge_proxy, {'from': alice})
    gauge_proxy.accept_transfer_ownership(gauge_v2, {'from': accounts[idx]})

    assert gauge_v2.admin() == gauge_proxy


def test_commit_transfer_ownership(alice, bob, gauge_proxy, gauge_v2):
    gauge_v2.commit_transfer_ownership(gauge_proxy, {'from': alice})
    gauge_proxy.accept_transfer_ownership(gauge_v2, {'from': alice})
    gauge_proxy.commit_transfer_ownership(gauge_v2, bob, {'from': alice})

    assert gauge_v2.future_admin() == bob


@pytest.mark.parametrize('idx', range(1, 4))
def test_commit_only_owner(alice, accounts, gauge_proxy, gauge_v2, idx):
    gauge_v2.commit_transfer_ownership(gauge_proxy, {'from': alice})
    gauge_proxy.accept_transfer_ownership(gauge_v2, {'from': alice})
    with brownie.reverts("Access denied"):
        gauge_proxy.commit_transfer_ownership(gauge_v2, alice, {'from': accounts[idx]})
