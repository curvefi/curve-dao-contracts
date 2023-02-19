import brownie
import pytest
from brownie import ETH_ADDRESS, Contract
from brownie_tokens import MintableForkToken, skip_holders

WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

swap_datas = [
    {
        "_from": "0xAf5191B0De278C7286d6C7CC6ab6BB8A73bA2Cd6",
        "_to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "_pool": "0x3211c6cbef1429da3d0d58494938299c92ad5860",
        "_i": 0,
        "_j": 1,
        "_is_tricrypto": False,
    },
    {
        "_from": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "_to": "0xAf5191B0De278C7286d6C7CC6ab6BB8A73bA2Cd6",
        "_pool": "0x3211c6cbef1429da3d0d58494938299c92ad5860",
        "_i": 1,
        "_j": 0,
        "_is_tricrypto": False,
    },
    {
        "_from": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "_to": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "_pool": "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46",
        "_i": 0,
        "_j": 1,
        "_is_tricrypto": True,
    },
    {
        "_from": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "_to": WETH,
        "_pool": "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46",
        "_i": 1,
        "_j": 2,
        "_is_tricrypto": True,
    },
    {
        "_from": WETH,
        "_to": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "_pool": "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46",
        "_i": 2,
        "_j": 0,
        "_is_tricrypto": True,
    },
]

swap_datas_eth = [
    {
        "_from": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "_to": ETH_ADDRESS,
        "_pool": "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46",
        "_i": 1,
        "_j": 2,
        "_is_tricrypto": True,
    },
    {
        "_from": ETH_ADDRESS,
        "_to": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "_pool": "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46",
        "_i": 2,
        "_j": 0,
        "_is_tricrypto": True,
    },
]


@pytest.fixture(scope="module")
def pool_proxy():
    yield Contract("0xeCb456EA5365865EbAb8a2661B0c503410e9B347")


@pytest.fixture(scope="module")
def burner(SwapCryptoBurner, pool_proxy, alice, receiver):
    yield SwapCryptoBurner.deploy(
        pool_proxy,  # pool_proxy
        alice,  # recovery
        alice,  # owner
        alice,  # emergency_owner
        {"from": alice},
    )


def _set_swap_data(burner, swap_data, pool_proxy, alice, receiver):
    burner.set_swap_data(
        swap_data["_from"],
        swap_data["_to"],
        swap_data["_pool"],
        receiver,
        swap_data["_i"],
        swap_data["_j"],
        swap_data["_is_tricrypto"],
        {"from": alice},
    )
    pool_proxy.set_burner(swap_data["_from"], burner, {"from": pool_proxy.ownership_admin()})
    skip_holders(swap_data["_pool"])


@pytest.mark.parametrize("swap_data", swap_datas)
def test_burn(burner, pool_proxy, swap_data, alice, receiver):
    _set_swap_data(burner, swap_data, pool_proxy, alice, receiver)

    coin = MintableForkToken(swap_data["_from"])
    amount = 10 * 10 ** coin.decimals()
    coin.transfer(alice, coin.balanceOf(pool_proxy), {"from": pool_proxy})
    coin._mint_for_testing(pool_proxy, amount, {"from": alice})

    coin_to = MintableForkToken(swap_data["_to"])
    initial_balance = coin_to.balanceOf(receiver)

    pool_proxy.burn(coin, {"from": alice})

    assert coin.balanceOf(pool_proxy) == 0
    assert coin_to.balanceOf(receiver) > initial_balance

    # Simple slippage check
    pool = Contract(swap_data["_pool"])
    amount = pool.balances(swap_data["_i"])
    coin._mint_for_testing(pool_proxy, amount // 5, {"from": alice})

    with brownie.reverts():
        pool_proxy.burn(coin, {"from": alice})


def _mint_exact_for_proxy(coin, amount, pool_proxy, alice):
    if coin == ETH_ADDRESS:
        alice.transfer(pool_proxy, amount)
        weth = MintableForkToken(WETH)
        weth.deposit({"from": pool_proxy, "value": pool_proxy.balance()})
        weth.withdraw(amount, {"from": pool_proxy})
    else:
        coin.transfer(alice, coin.balanceOf(pool_proxy), {"from": pool_proxy})
        coin._mint_for_testing(pool_proxy, amount, {"from": alice})


def _get_balance(coin, of):
    return of.balance() if coin == ETH_ADDRESS else coin.balanceOf(of)


@pytest.mark.parametrize("swap_data", swap_datas_eth)
def test_burn_eth(burner, pool_proxy, swap_data, alice, receiver):
    _set_swap_data(burner, swap_data, pool_proxy, alice, receiver)

    coin = (
        MintableForkToken(swap_data["_from"]) if swap_data["_from"] != ETH_ADDRESS else ETH_ADDRESS
    )
    amount = 10 * 10 ** coin.decimals() if swap_data["_from"] != ETH_ADDRESS else 10 ** 18
    _mint_exact_for_proxy(coin, amount, pool_proxy, alice)

    if swap_data["_to"] == ETH_ADDRESS:
        coin_to = ETH_ADDRESS
        initial_balance = receiver.balance()
    else:
        coin_to = MintableForkToken(swap_data["_to"])
        initial_balance = coin_to.balanceOf(receiver)

    pool_proxy.burn(coin, {"from": alice})

    assert _get_balance(coin, pool_proxy) == 0
    assert _get_balance(coin_to, receiver) > initial_balance

    # Simple slippage check
    pool = Contract(swap_data["_pool"])
    amount = pool.balances(swap_data["_i"])
    _mint_exact_for_proxy(coin, amount // 5, pool_proxy, alice)

    with brownie.reverts():
        pool_proxy.burn(swap_data["_from"], {"from": alice})
