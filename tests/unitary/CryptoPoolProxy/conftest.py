import pytest


@pytest.fixture(scope="module", autouse=True)
def admin_setup(accounts, chain, crypto_pool_proxy, crypto_pool):
    # set admins as accounts[:3]
    crypto_pool_proxy.commit_set_admins(
        accounts[0], accounts[1], accounts[2], {"from": accounts[0]}
    )
    crypto_pool_proxy.apply_set_admins({"from": accounts[0]})

    # set crypto_pool_proxy as owner of crypto_pool
    crypto_pool.commit_transfer_ownership(crypto_pool_proxy, {"from": accounts[0]})
    chain.sleep(3 * 86400)
    crypto_pool.apply_transfer_ownership({"from": accounts[0]})
