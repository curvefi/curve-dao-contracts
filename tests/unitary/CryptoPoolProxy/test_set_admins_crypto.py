import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_set_admins(accounts, crypto_pool_proxy):
    crypto_pool_proxy.commit_set_admins(
        accounts[1], accounts[2], accounts[3], {"from": accounts[0]}
    )
    crypto_pool_proxy.apply_set_admins()

    assert crypto_pool_proxy.ownership_admin() == accounts[1]
    assert crypto_pool_proxy.parameter_admin() == accounts[2]
    assert crypto_pool_proxy.emergency_admin() == accounts[3]


@pytest.mark.parametrize("idx", range(1, 4))
def test_set_admins_no_access(accounts, crypto_pool_proxy, idx):
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.commit_set_admins(
            accounts[1], accounts[2], accounts[3], {"from": accounts[idx]}
        )
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.apply_set_admins({"from": accounts[idx]})
