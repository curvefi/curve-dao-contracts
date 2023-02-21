import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS, Contract
from brownie_tokens import MintableForkToken, skip_holders

WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

swap_datas = [
    {
        "_from": "0x853d955aCEf822Db058eb8505911ED77F175b99e",
        "_to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "_pool": "0xDcEF968d416a41Cdac0ED8702fAC8128A64241A2",
        "_i": 0,
        "_j": 1,
    },
    {
        "_from": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "_to": "0x853d955aCEf822Db058eb8505911ED77F175b99e",
        "_pool": "0xDcEF968d416a41Cdac0ED8702fAC8128A64241A2",
        "_i": 1,
        "_j": 0,
    },
    {
        "_from": ETH_ADDRESS,
        "_to": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
        "_pool": "0xDC24316b9AE028F1497c275EB9192a3Ea0f67022",
        "_i": 0,
        "_j": 1,
    },
    {
        "_from": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
        "_to": ETH_ADDRESS,
        "_pool": "0xDC24316b9AE028F1497c275EB9192a3Ea0f67022",
        "_i": 1,
        "_j": 0,
    },
]


@pytest.fixture(scope="module")
def pool_proxy():
    yield Contract("0xeCb456EA5365865EbAb8a2661B0c503410e9B347")


@pytest.fixture(scope="module")
def burner(SwapStableBurner, alice, receiver):
    yield SwapStableBurner.deploy(
        alice,  # recovery
        alice,  # owner
        alice,  # emergency_owner
        {"from": alice},
    )


@pytest.fixture(scope="module", autouse=True)
def setup(burner, pool_proxy, alice, receiver):
    froms = [data["_from"] for data in swap_datas]
    datas = [(data["_pool"], data["_to"], receiver, data["_i"], data["_j"]) for data in swap_datas]
    burner.set_many_swap_data(froms, datas)

    to_pad = [ZERO_ADDRESS] * (20 - len(froms))
    ownership_admin = pool_proxy.ownership_admin()
    pool_proxy.set_many_burners(
        froms + to_pad, [burner] * len(froms) + to_pad, {"from": ownership_admin}
    )
    skip_holders(*[swap_data["_pool"] for swap_data in swap_datas])


def _get_balance(coin, of):
    return of.balance() if coin == ETH_ADDRESS else coin.balanceOf(of)


@pytest.mark.parametrize("swap_data", swap_datas)
def test_burn(burner, pool_proxy, swap_data, alice, receiver):
    if swap_data["_from"] == ETH_ADDRESS:
        coin = ETH_ADDRESS
        amount = 10 ** 18
        alice.transfer(pool_proxy, amount)
        weth = MintableForkToken(WETH)
        weth.deposit({"from": pool_proxy, "value": pool_proxy.balance()})
        weth.withdraw(amount, {"from": pool_proxy})
    else:
        coin = MintableForkToken(swap_data["_from"])
        amount = 10 * 10 ** coin.decimals()
        coin.transfer(alice, coin.balanceOf(pool_proxy), {"from": pool_proxy})
        coin._mint_for_testing(pool_proxy, amount, {"from": alice})

    if swap_data["_to"] == ETH_ADDRESS:
        coin_to = ETH_ADDRESS
        initial_balance = receiver.balance()
    else:
        coin_to = MintableForkToken(swap_data["_to"])
        initial_balance = coin_to.balanceOf(receiver)

    pool_proxy.burn(coin, {"from": alice})

    assert _get_balance(coin, pool_proxy) <= amount // 10 ** 6
    assert _get_balance(coin_to, receiver) > initial_balance
