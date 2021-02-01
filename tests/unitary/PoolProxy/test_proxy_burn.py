import brownie
import pytest

ETH_ADDRESS = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

burner_mock = """
# @version 0.2.7

is_burned: public(HashMap[address, bool])

@payable
@external
def burn(coin: address) -> bool:
    self.is_burned[coin] = True
    return True
"""


@pytest.fixture(scope="module")
def burner(accounts, pool_proxy, coin_a):
    contract = brownie.compile_source(burner_mock).Vyper.deploy({"from": accounts[0]})
    pool_proxy.set_burner(coin_a, contract, {"from": accounts[0]})
    pool_proxy.set_burner(ETH_ADDRESS, contract, {"from": accounts[0]})
    accounts[0].transfer(pool_proxy, 31337)

    yield contract


@pytest.mark.parametrize("idx", range(2))
def test_burn(accounts, pool_proxy, burner, coin_a, idx):
    pool_proxy.burn(coin_a, {"from": accounts[idx]})

    assert burner.is_burned(coin_a)
    assert pool_proxy.balance() == 31337
    assert burner.balance() == 0


@pytest.mark.parametrize("idx", range(2))
def test_burn_eth(accounts, pool_proxy, burner, idx):
    pool_proxy.burn(ETH_ADDRESS, {"from": accounts[idx]})

    assert burner.is_burned(ETH_ADDRESS)
    assert pool_proxy.balance() == 0
    assert burner.balance() == 31337


@pytest.mark.parametrize("idx", range(2))
def test_burn_many(accounts, pool_proxy, burner, coin_a, idx):
    pool_proxy.burn_many([coin_a, ETH_ADDRESS] + [ZERO_ADDRESS] * 18, {"from": accounts[0]})

    assert burner.is_burned(coin_a)
    assert burner.is_burned(ETH_ADDRESS)

    assert pool_proxy.balance() == 0
    assert burner.balance() == 31337


def test_burn_not_exists(accounts, pool_proxy):
    with brownie.reverts("dev: should implement burn()"):
        pool_proxy.burn(accounts[1], {"from": accounts[0]})


def test_burn_many_not_exists(accounts, pool_proxy, burner, coin_a):
    with brownie.reverts("dev: should implement burn()"):
        pool_proxy.burn_many(
            [coin_a, ETH_ADDRESS, accounts[1]] + [ZERO_ADDRESS] * 17, {"from": accounts[0]},
        )
