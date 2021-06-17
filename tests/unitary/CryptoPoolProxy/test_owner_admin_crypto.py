import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
DAY = 86400


owner_functions_mock = """
# @version 0.2.7

aave: public(uint256)
donated: public(bool)
withdrawn: public(uint256)

@payable
@external
def __default__():
    pass

@external
def set_aave_referral(referral_code: uint256):
    self.aave = referral_code

@external
def donate_admin_fees():
    self.donated = True

@external
def claim_admin_fees():
    if self.balance > 0:
        send(msg.sender, self.balance)
    self.withdrawn += 1
"""


@pytest.fixture(scope="module")
def owner_pool(accounts):
    yield brownie.compile_source(owner_functions_mock).Vyper.deploy({"from": accounts[0]})


def test_transfer_ownership(accounts, chain, crypto_pool_proxy, crypto_pool):
    crypto_pool_proxy.commit_transfer_ownership(crypto_pool, accounts[4], {"from": accounts[0]})
    chain.sleep(DAY * 3)
    crypto_pool_proxy.apply_transfer_ownership(crypto_pool, {"from": accounts[0]})

    assert crypto_pool.owner() == accounts[4]


@pytest.mark.parametrize("idx", range(1, 4))
def test_commit_transfer_ownership_no_access(accounts, crypto_pool_proxy, crypto_pool, idx):
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.commit_transfer_ownership(
            crypto_pool, accounts[4], {"from": accounts[idx]}
        )


@pytest.mark.parametrize("idx", range(0, 4))
def test_apply_transfer_ownership_no_access(accounts, chain, crypto_pool_proxy, crypto_pool, idx):
    crypto_pool_proxy.commit_transfer_ownership(crypto_pool, accounts[4], {"from": accounts[0]})
    chain.sleep(DAY * 3)
    crypto_pool_proxy.apply_transfer_ownership(crypto_pool, {"from": accounts[idx]})


def test_cancel_transfer_ownership(accounts, crypto_pool_proxy, crypto_pool):
    crypto_pool_proxy.commit_transfer_ownership(crypto_pool, accounts[4], {"from": accounts[0]})
    crypto_pool_proxy.revert_transfer_ownership(crypto_pool, {"from": accounts[0]})

    with brownie.reverts():
        crypto_pool_proxy.apply_transfer_ownership(crypto_pool, {"from": accounts[0]})


def test_cancel_transfer_ownership_no_access(accounts, crypto_pool_proxy, crypto_pool):
    crypto_pool_proxy.commit_transfer_ownership(crypto_pool, accounts[4], {"from": accounts[0]})
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.revert_transfer_ownership(crypto_pool, {"from": accounts[4]})


def test_set_aave_referral(accounts, crypto_pool_proxy, owner_pool):
    crypto_pool_proxy.set_aave_referral(owner_pool, 42, {"from": accounts[0]})

    assert owner_pool.aave() == 42


@pytest.mark.xfail
def test_set_aave_referral_not_exists(accounts, crypto_pool_proxy, crypto_pool):
    # current crypto pool utilizes
    with brownie.reverts():
        crypto_pool_proxy.set_aave_referral(crypto_pool, 42, {"from": accounts[0]})


@pytest.mark.parametrize("idx", range(1, 4))
def test_set_aave_referral_no_access(accounts, crypto_pool_proxy, owner_pool, idx):
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.set_aave_referral(owner_pool, 42, {"from": accounts[idx]})


def test_donate_fees(accounts, crypto_pool_proxy, owner_pool):
    crypto_pool_proxy.donate_admin_fees(owner_pool, {"from": accounts[0]})

    assert owner_pool.donated() is True


@pytest.mark.xfail
def test_donate_fees_not_exists(accounts, crypto_pool_proxy, crypto_pool):
    with brownie.reverts():
        crypto_pool_proxy.donate_admin_fees(crypto_pool, {"from": accounts[0]})


@pytest.mark.parametrize("idx", range(1, 4))
def test_donate_fees_no_access(accounts, crypto_pool_proxy, owner_pool, idx):
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.donate_admin_fees(owner_pool, {"from": accounts[idx]})


@pytest.mark.parametrize("idx", range(4))
def test_withdraw_admin_fees(accounts, crypto_pool_proxy, owner_pool, idx):
    crypto_pool_proxy.withdraw_admin_fees(owner_pool, {"from": accounts[idx]})

    assert owner_pool.withdrawn() == 1


def test_withdraw_admin_fees_receive_eth(accounts, crypto_pool_proxy, owner_pool):
    accounts[0].transfer(owner_pool, 31337)
    crypto_pool_proxy.withdraw_admin_fees(owner_pool, {"from": accounts[0]})

    assert owner_pool.withdrawn() == 1
    assert crypto_pool_proxy.balance() == 31337


def test_withdraw_many(accounts, crypto_pool_proxy, owner_pool):
    accounts[0].transfer(owner_pool, 31337)
    crypto_pool_proxy.withdraw_many([owner_pool] * 5 + [ZERO_ADDRESS] * 15, {"from": accounts[0]})

    assert owner_pool.withdrawn() == 5
    assert crypto_pool_proxy.balance() == 31337


@pytest.mark.parametrize("idx", range(1, 4))
def test_set_burner_no_access(accounts, crypto_pool_proxy, token, idx):
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.set_burner(token, accounts[1], {"from": accounts[idx]})


def test_set_burner(accounts, crypto_pool_proxy, token):
    crypto_pool_proxy.set_burner(token, accounts[4], {"from": accounts[0]})

    assert token.allowance(crypto_pool_proxy, accounts[4]) == 2 ** 256 - 1


def test_unset_burner(accounts, crypto_pool_proxy, token):
    crypto_pool_proxy.set_burner(token, accounts[4], {"from": accounts[0]})
    crypto_pool_proxy.set_burner(token, ZERO_ADDRESS, {"from": accounts[0]})

    assert token.allowance(crypto_pool_proxy, accounts[4]) == 0


def test_modify_burner(accounts, crypto_pool_proxy, token):
    crypto_pool_proxy.set_burner(token, accounts[4], {"from": accounts[0]})
    crypto_pool_proxy.set_burner(token, accounts[5], {"from": accounts[0]})

    assert token.allowance(crypto_pool_proxy, accounts[4]) == 0
    assert token.allowance(crypto_pool_proxy, accounts[5]) == 2 ** 256 - 1
