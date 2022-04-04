import brownie
import pytest
from brownie import ZERO_ADDRESS
from brownie_tokens import MintableForkToken

coins = {
    "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "yfi": "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
    "stg": "0xAf5191B0De278C7286d6C7CC6ab6BB8A73bA2Cd6",
    "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "btrfly": "0xC0d4Ceb216B3BA9C3701B291766fDCbA977ceC3A",
}

tokens = {
    "yfieth": "0x29059568bB40344487d62f7450E78b8E6C74e0e5",
    "stgusdc": "0xdf55670e27bE5cDE7228dD0A6849181891c9ebA1",
    "ethbtrfly": "0xE160364FD8407FFc8b163e278300c6C5D18Ff61d",
    "badgerwbtc": "0x137469B55D1f15651BA46A89D0588e97dD0B6562",
}


@pytest.fixture(scope="module")
def burner(CryptoFactoryLPBurner, alice, receiver):
    yield CryptoFactoryLPBurner.deploy(receiver, alice, alice, alice, {"from": alice})


@pytest.fixture(scope="module", autouse=True)
def setup(burner, alice):
    prioritized = [coins["weth"], coins["usdc"], coins["btrfly"]]
    priorities = [10, 10, 10]
    burner.set_many_priorities(
        prioritized + [ZERO_ADDRESS] * (8 - len(prioritized)),
        priorities + [0] * (8 - len(priorities)),
        {"from": alice},
    )


def test_first_coin(burner, alice, receiver):
    token = MintableForkToken(tokens["yfieth"])
    token.approve(burner, 2 ** 256 - 1, {"from": alice})
    token._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    burner.burn(token, {"from": alice})

    first, second = MintableForkToken(coins["weth"]), MintableForkToken(coins["yfi"])
    assert first.balanceOf(receiver) == 0
    assert receiver.balance() > 0
    assert second.balanceOf(receiver) == 0


def test_second_coin(burner, alice, receiver):
    token = MintableForkToken(tokens["stgusdc"])
    token.approve(burner, 2 ** 256 - 1, {"from": alice})
    token._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    burner.burn(token, {"from": alice})

    first, second = MintableForkToken(coins["stg"]), MintableForkToken(coins["usdc"])
    assert first.balanceOf(receiver) == 0
    assert second.balanceOf(receiver) > 0


def test_both_coins(burner, alice, receiver):
    token = MintableForkToken(tokens["ethbtrfly"])
    token.approve(burner, 2 ** 256 - 1, {"from": alice})
    token._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    burner.burn(token, {"from": alice})

    first, second = MintableForkToken(coins["weth"]), MintableForkToken(coins["btrfly"])
    assert first.balanceOf(receiver) == 0
    assert receiver.balance() > 0
    assert second.balanceOf(receiver) > 0


def test_set_priority(burner, alice):
    coin = coins["weth"]
    assert burner.priority(coin) == 10
    burner.set_priority(coin, 0, {"from": alice})
    assert burner.priority(coin) == 0


@pytest.mark.parametrize("i", [0, 1])
def test_more_prioritized(burner, alice, receiver, i):
    token = MintableForkToken(tokens["ethbtrfly"])
    token.approve(burner, 2 ** 256 - 1, {"from": alice})
    token._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    first, second = MintableForkToken(coins["weth"]), MintableForkToken(coins["btrfly"])
    burner.set_priority(first if i == 0 else second, 100, {"from": alice})

    burner.burn(token, {"from": alice})

    assert first.balanceOf(receiver) == 0
    if i == 0:
        assert receiver.balance() > 0
        assert second.balanceOf(receiver) == 0
    else:
        assert receiver.balance() == 0
        assert second.balanceOf(receiver) > 0


def test_unkown_priorities(burner, alice):
    token = MintableForkToken(tokens["badgerwbtc"])
    token.approve(burner, 2 ** 256 - 1, {"from": alice})
    token._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    with brownie.reverts():
        burner.burn(token, {"from": alice})
