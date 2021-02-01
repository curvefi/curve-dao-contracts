import pytest


@pytest.fixture(scope="module")
def burner(UnderlyingBurner, alice, receiver):
    yield UnderlyingBurner.deploy(receiver, receiver, alice, alice, {"from": alice})


tripool = (
    ("0x6B175474E89094C44Da98b954EedeAC495271d0F", "DAI"),
    ("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "USDC"),
    ("0xdAC17F958D2ee523a2206206994597C13D831ec7", "USDT"),
)

swapped = (
    ("0x8e870d67f660d95d5be530380d0ec0bd388289e1", "PAX"),
    ("0x57ab1ec28d129707052df4df418d58a2d46d5f51", "sUSD"),
)


@pytest.mark.parametrize("token", [i[0] for i in tripool], ids=[i[1] for i in tripool])
@pytest.mark.parametrize("burner_balance", (True, False))
@pytest.mark.parametrize("caller_balance", (True, False))
def test_burn_no_swap(
    MintableTestToken, alice, receiver, burner, token, burner_balance, caller_balance
):
    coin = MintableTestToken(token)
    amount = 10 ** coin.decimals()

    if caller_balance:
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(burner, 2 ** 256 - 1, {"from": alice})

    if burner_balance:
        coin._mint_for_testing(burner, amount, {"from": alice})
        amount *= 2

    burner.burn(coin, {"from": alice})

    if burner_balance or caller_balance:
        assert coin.balanceOf(alice) == 0
        assert coin.balanceOf(burner) == amount
        assert coin.balanceOf(receiver) == 0


@pytest.mark.parametrize("token", [i[0] for i in swapped], ids=[i[1] for i in swapped])
@pytest.mark.parametrize("has_balance", (True, False))
def test_burn_swap(MintableTestToken, USDC, alice, receiver, burner, token, has_balance):
    coin = MintableTestToken(token)
    amount = 10 ** coin.decimals()

    coin._mint_for_testing(alice, amount, {"from": alice})
    coin.approve(burner, 2 ** 256 - 1, {"from": alice})

    if has_balance:
        coin._mint_for_testing(burner, amount, {"from": alice})

    burner.burn(coin, {"from": alice})

    assert coin.balanceOf(alice) == 0
    assert coin.balanceOf(burner) == 0
    assert coin.balanceOf(receiver) == 0

    assert USDC.balanceOf(alice) == 0
    assert USDC.balanceOf(burner) > 0
    assert USDC.balanceOf(receiver) == 0


def test_execute(MintableTestToken, ThreeCRV, alice, burner, receiver):
    coins = [MintableTestToken(i[0]) for i in tripool]
    for coin in coins:
        amount = 10 ** coin.decimals()
        coin._mint_for_testing(burner, amount, {"from": alice})

    burner.execute({"from": alice})

    for coin in coins:
        assert coin.balanceOf(alice) == 0
        assert coin.balanceOf(burner) == 0
        assert coin.balanceOf(receiver) == 0

    assert ThreeCRV.balanceOf(alice) == 0
    assert ThreeCRV.balanceOf(burner) == 0
    assert ThreeCRV.balanceOf(receiver) > 0
