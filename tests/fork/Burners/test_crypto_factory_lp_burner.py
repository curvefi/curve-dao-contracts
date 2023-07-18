import brownie
import pytest
from brownie import ZERO_ADDRESS, Contract
from brownie_tokens import MintableForkToken

coins = {
    "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "yfi": "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
    "stg": "0xAf5191B0De278C7286d6C7CC6ab6BB8A73bA2Cd6",
    "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "btrfly": "0xc55126051B22eBb829D00368f4B12Bde432de5Da",
}

tokens = {
    "yfieth": "0x29059568bB40344487d62f7450E78b8E6C74e0e5",
    "stgusdc": "0xdf55670e27bE5cDE7228dD0A6849181891c9ebA1",
    "btrflyeth": "0x7483Dd57f6488b0e194A151C57Df6Ec85C00aCE9",
    "badgerwbtc": "0x137469B55D1f15651BA46A89D0588e97dD0B6562",
}


@pytest.fixture(scope="module")
def pool_proxy():
    yield Contract("0xeCb456EA5365865EbAb8a2661B0c503410e9B347")


@pytest.fixture(scope="module")
def burner(CryptoFactoryLPBurner, pool_proxy, alice, receiver):
    yield CryptoFactoryLPBurner.deploy(
        pool_proxy,  # pool_proxy
        receiver,  # receiver
        alice,  # recovery
        alice,  # owner
        alice,  # emergency_owner
        {"from": alice},
    )


@pytest.fixture(scope="module", autouse=True)
def setup(burner, alice):
    prioritized = [coins["weth"], coins["usdc"], coins["btrfly"]]
    priorities = [10, 10, 10]
    burner.set_many_priorities(
        prioritized + [ZERO_ADDRESS] * (8 - len(prioritized)),
        priorities + [0] * (8 - len(priorities)),
        {"from": alice},
    )


def test_set_slippage(burner, alice, bob):
    assert burner.slippage() == 100
    burner.set_slippage(200, {"from": alice})
    assert burner.slippage() == 200
    with brownie.reverts():  # only owner
        burner.set_slippage(10, {"from": bob})


def test_set_priority(burner, alice, bob):
    coin = coins["weth"]
    assert burner.priority_of(coin) == 10
    burner.set_priority_of(coin, 0, {"from": alice})
    assert burner.priority_of(coin) == 0
    with brownie.reverts():  # only manager
        burner.set_priority_of(coin, 1, {"from": bob})


def test_set_receivers(burner, alice, bob, pool_proxy, receiver):
    assert burner.receiver_of(coins["weth"]) == ZERO_ADDRESS
    burner.set_receiver_of(coins["weth"], bob)
    assert burner.receiver_of(coins["weth"]) == bob.address
    with brownie.reverts():  # only admin
        burner.set_receiver_of(coins["weth"], bob, {"from": bob})

    coins_with_custom_receiver = [coins["weth"], coins["usdc"]]
    burner.set_many_receivers(
        coins_with_custom_receiver + [ZERO_ADDRESS] * (8 - len(coins_with_custom_receiver)),
        [pool_proxy] * len(coins_with_custom_receiver)
        + [ZERO_ADDRESS] * (8 - len(coins_with_custom_receiver)),
        {"from": alice},
    )
    for coin in coins_with_custom_receiver:
        assert burner.receiver_of(coin) == pool_proxy
    with brownie.reverts():  # only admin
        burner.set_many_receivers(
            [coins["weth"]] + [ZERO_ADDRESS] * (8 - 1),
            [bob] + [ZERO_ADDRESS] * (8 - 1),
            {"from": bob},
        )

    assert burner.receiver() == receiver
    burner.set_receiver(pool_proxy)
    assert burner.receiver() == pool_proxy
    with brownie.reverts():  # only admin
        burner.set_receiver(bob, {"from": bob})


@pytest.mark.parametrize("final_receiver", ["receiver", "bob"])
def test_first_coin(burner, alice, bob, receiver, final_receiver):
    initial_bob_balance = bob.balance()
    token = MintableForkToken(tokens["yfieth"])
    token.approve(burner, 2 ** 256 - 1, {"from": alice})
    token._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    first, second = MintableForkToken(coins["weth"]), MintableForkToken(coins["yfi"])
    if final_receiver == "bob":
        burner.set_receiver_of(first, bob, {"from": alice})
    burner.burn(token, {"from": alice})

    for acc in [bob, receiver]:
        assert first.balanceOf(acc) == 0
        assert second.balanceOf(acc) == 0
    if final_receiver == "bob":
        assert receiver.balance() == 0
        assert bob.balance() > initial_bob_balance
    else:
        assert receiver.balance() > 0
        assert bob.balance() == initial_bob_balance


def test_second_coin(burner, alice, receiver):
    token = MintableForkToken(tokens["stgusdc"])
    token.approve(burner, 2 ** 256 - 1, {"from": alice})
    token._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    burner.burn(token, {"from": alice})

    first, second = MintableForkToken(coins["stg"]), MintableForkToken(coins["usdc"])
    assert first.balanceOf(receiver) == 0
    assert second.balanceOf(receiver) > 0


def test_both_coins(burner, alice, receiver):
    token = MintableForkToken(tokens["btrflyeth"])
    token.approve(burner, 2 ** 256 - 1, {"from": alice})
    token._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    burner.burn(token, {"from": alice})

    first, second = MintableForkToken(coins["weth"]), MintableForkToken(coins["btrfly"])
    assert first.balanceOf(receiver) == 0
    assert receiver.balance() > 0
    assert second.balanceOf(receiver) > 0


@pytest.mark.parametrize("i", [0, 1])
def test_more_prioritized(burner, alice, receiver, i):
    token = MintableForkToken(tokens["btrflyeth"])
    token.approve(burner, 2 ** 256 - 1, {"from": alice})
    token._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    first, second = MintableForkToken(coins["weth"]), MintableForkToken(coins["btrfly"])
    burner.set_priority_of(first if i == 0 else second, 100, {"from": alice})

    burner.burn(token, {"from": alice})

    assert first.balanceOf(receiver) == 0
    if i == 0:
        assert receiver.balance() > 0
        assert second.balanceOf(receiver) == 0
    else:
        assert receiver.balance() == 0
        assert second.balanceOf(receiver) > 0


def test_burn_amount(burner, pool_proxy, alice, receiver):
    token = MintableForkToken(tokens["stgusdc"])
    amount = 10 * 10 ** 18

    pool_proxy.set_burner(token, burner, {"from": pool_proxy.ownership_admin()})
    token._mint_for_testing(pool_proxy, amount, {"from": alice})
    amount = token.balanceOf(pool_proxy)

    burner.burn_amount(token, amount // 2, {"from": alice})
    assert token.balanceOf(burner) == amount - amount // 2

    first, second = MintableForkToken(coins["stg"]), MintableForkToken(coins["usdc"])
    assert first.balanceOf(receiver) == 0
    assert second.balanceOf(receiver) > 0


def test_unkown_priorities(burner, alice):
    token = MintableForkToken(tokens["badgerwbtc"])
    token.approve(burner, 2 ** 256 - 1, {"from": alice})
    token._mint_for_testing(alice, 10 * 10 ** 18, {"from": alice})

    with brownie.reverts():
        burner.burn(token, {"from": alice})


def test_manager(burner, alice, bob, charlie):
    # Initial
    assert burner.manager() == alice
    assert burner.future_manager() == ZERO_ADDRESS

    burner.commit_new_manager(bob, {"from": alice})
    assert burner.manager() == alice
    assert burner.future_manager() == bob

    burner.accept_new_manager({"from": bob})
    assert burner.manager() == bob
    assert burner.future_manager() == bob

    # Manager has access
    burner.set_priority_of(coins["weth"], 0, {"from": bob})
    assert burner.priority_of(coins["weth"]) == 0
    burner.set_many_priorities(
        [coins["weth"], coins["usdc"]] + [ZERO_ADDRESS] * 6,
        [1, 2] + [0] * 6,
        {"from": bob},
    )
    assert burner.priority_of(coins["weth"]) == 1
    assert burner.priority_of(coins["usdc"]) == 2

    burner.commit_new_manager(charlie, {"from": bob})
    burner.accept_new_manager({"from": charlie})

    # Old manager does not have access
    with brownie.reverts():
        burner.set_priority_of(coins["weth"], 0, {"from": bob})
    with brownie.reverts():
        burner.set_many_priorities(
            [coins["weth"], coins["usdc"]] + [ZERO_ADDRESS] * 6,
            [1, 2] + [0] * 6,
            {"from": bob},
        )
    with brownie.reverts():
        burner.set_slippage_of(coins["weth"], 0, {"from": bob})
    with brownie.reverts():
        burner.set_many_slippages(
            [coins["weth"], coins["usdc"]] + [ZERO_ADDRESS] * 6,
            [1, 2] + [0] * 6,
            {"from": bob},
        )
