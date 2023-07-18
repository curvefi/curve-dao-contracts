import pytest
from brownie import ZERO_ADDRESS, Contract
from brownie_tokens import MintableForkToken

coins = {
    "usdt": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "wsteth": "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0",
    "wbtc": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "crvusd": "0xf939e0a03fb07f59a73314e73794be0e57ac1b4e",
    "tbtc": "0x18084fba666a33d37592fa2633fd49a74dd93a88",
}


@pytest.fixture(scope="module")
def pool_proxy():
    yield Contract("0xeCb456EA5365865EbAb8a2661B0c503410e9B347")


@pytest.fixture(scope="module")
def burner(TricryptoFactoryLPBurner, pool_proxy, alice, receiver):
    contract = TricryptoFactoryLPBurner.deploy(
        pool_proxy,  # pool_proxy
        alice,  # owner
        alice,  # emergency_owner
        {"from": alice},
    )
    contract.set_receiver(receiver, {"from": alice})
    yield contract


@pytest.fixture(scope="module", autouse=True)
def setup(burner, alice):
    prioritized = [coins["usdt"], coins["wbtc"], coins["wsteth"]]
    priorities = [156, 148, 140]
    burner.set_many_priorities(
        prioritized + [ZERO_ADDRESS] * (8 - len(prioritized)),
        priorities + [0] * (8 - len(priorities)),
        {"from": alice},
    )


def test_first_coin(burner, alice, receiver):
    pool = MintableForkToken("0xf5f5b97624542d72a9e06f04804bf81baa15e2b4")  # TricryptoUSDT
    pool.approve(burner, 2 ** 256 - 1, {"from": alice})
    pool._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    target = MintableForkToken(coins["usdt"])
    others = [
        MintableForkToken(coins["wbtc"]),
        MintableForkToken(coins["weth"]),
    ]

    burner.burn(pool, {"from": alice})

    for acc in [burner, receiver]:
        for coin in others:
            assert coin.balanceOf(acc) == 0
    assert target.balanceOf(burner) == 0
    assert target.balanceOf(receiver) > 0


def test_second_coin(burner, alice, receiver):
    pool = MintableForkToken("0x7f86bf177dd4f3494b841a37e810a34dd56c829b")  # TricryptoUSDC
    pool.approve(burner, 2 ** 256 - 1, {"from": alice})
    pool._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    target = MintableForkToken(coins["wbtc"])
    others = [
        MintableForkToken(coins["usdc"]),
        MintableForkToken(coins["weth"]),
    ]

    burner.burn(pool, {"from": alice})

    for acc in [burner, receiver]:
        for coin in others:
            assert coin.balanceOf(acc) == 0
    assert target.balanceOf(burner) == 0
    assert target.balanceOf(receiver) > 0


def test_third_coins(burner, alice, receiver):
    pool = MintableForkToken("0x2889302a794da87fbf1d6db415c1492194663d13")  # TricryptoLLAMA
    pool.approve(burner, 2 ** 256 - 1, {"from": alice})
    pool._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    target = MintableForkToken(coins["wsteth"])
    others = [
        MintableForkToken(coins["crvusd"]),
        MintableForkToken(coins["tbtc"]),
    ]

    burner.burn(pool, {"from": alice})

    for acc in [burner, receiver]:
        for coin in others:
            assert coin.balanceOf(acc) == 0
    assert target.balanceOf(burner) == 0
    assert target.balanceOf(receiver) > 0
