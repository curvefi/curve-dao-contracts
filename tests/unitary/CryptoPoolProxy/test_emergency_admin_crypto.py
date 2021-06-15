import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_kill(accounts, crypto_pool_proxy, crypto_pool):
    crypto_pool_proxy.kill_me(crypto_pool, {"from": accounts[2]})


@pytest.mark.parametrize("idx", [0, 2])
def test_unkill(accounts, crypto_pool_proxy, crypto_pool, idx):
    crypto_pool_proxy.unkill_me(crypto_pool, {"from": accounts[idx]})


@pytest.mark.parametrize("idx", [0, 1, 3])
def test_kill_no_access(accounts, crypto_pool_proxy, crypto_pool, idx):
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.kill_me(crypto_pool, {"from": accounts[idx]})


@pytest.mark.parametrize("idx", [1, 3])
def test_unkill_no_access(accounts, crypto_pool_proxy, crypto_pool, idx):
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.unkill_me(crypto_pool, {"from": accounts[idx]})
