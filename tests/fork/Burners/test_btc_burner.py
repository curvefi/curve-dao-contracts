import pytest


@pytest.fixture(scope="module")
def burner(BTCBurner, alice, receiver):
    yield BTCBurner.deploy(receiver, receiver, alice, alice, {"from": alice})


tokens = (
    ("0xeb4c2781e4eba804ce9a9803c67d0893436bb27d", "rebBTC"),
    ("0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", "wBTC"),
    ("0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6", "sBTC"),
    ("0x0316EB71485b0Ab14103307bf65a021042c6d380", "hBTC"),
    ("0x8dAEBADE922dF735c38C80C7eBD708Af50815fAa", "tBTC"),
    # ("0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3", "sbtcCRV"),
)


@pytest.mark.parametrize("token", [i[0] for i in tokens], ids=[i[1] for i in tokens])
@pytest.mark.parametrize("burner_balance", (True, False))
@pytest.mark.parametrize("caller_balance", (True, False))
def test_swap(
    MintableTestToken, SUSD, alice, receiver, burner, token, burner_balance, caller_balance,
):
    coin = MintableTestToken(token)
    amount = 10 ** coin.decimals()

    if caller_balance:
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(burner, 2 ** 256 - 1, {"from": alice})

    if burner_balance:
        coin._mint_for_testing(burner, amount, {"from": alice})

    burner.burn(coin, {"from": alice})

    if burner_balance or caller_balance:
        assert coin.balanceOf(alice) == 0
        assert coin.balanceOf(burner) == 0
        assert coin.balanceOf(receiver) == 0

        assert SUSD.balanceOf(alice) == 0
        assert SUSD.balanceOf(burner) > 0
        assert SUSD.balanceOf(receiver) == 0


def test_execute(SUSD, USDC, alice, burner, receiver):
    SUSD._mint_for_testing(burner, 10 ** 18, {"from": alice})

    burner.execute({"from": alice})

    assert SUSD.balanceOf(alice) == 0
    assert SUSD.balanceOf(burner) == 0
    assert SUSD.balanceOf(receiver) == 0

    assert USDC.balanceOf(alice) == 0
    assert USDC.balanceOf(burner) == 0
    assert USDC.balanceOf(receiver) > 0


@pytest.mark.parametrize("token", [i[0] for i in tokens], ids=[i[1] for i in tokens])
def test_swap_and_execute(MintableTestToken, SUSD, USDC, alice, receiver, burner, token, chain):
    coin = MintableTestToken(token)
    amount = 10 ** coin.decimals()

    coin._mint_for_testing(alice, amount, {"from": alice})
    coin.approve(burner, 2 ** 256 - 1, {"from": alice})

    burner.burn(coin, {"from": alice})

    chain.sleep(300)

    burner.execute({"from": alice})

    assert coin.balanceOf(alice) == 0
    assert coin.balanceOf(burner) == 0
    assert coin.balanceOf(receiver) == 0

    assert SUSD.balanceOf(alice) == 0
    assert SUSD.balanceOf(burner) == 0
    assert SUSD.balanceOf(receiver) == 0

    assert USDC.balanceOf(alice) == 0
    assert USDC.balanceOf(burner) == 0
    assert USDC.balanceOf(receiver) > 0
