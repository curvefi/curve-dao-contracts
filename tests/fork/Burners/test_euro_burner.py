import pytest


@pytest.fixture(scope="module")
def burner(EuroBurner, alice, receiver):
    yield EuroBurner.deploy(receiver, receiver, alice, alice, {'from': alice})


tokens = (
    ("0xdB25f211AB05b1c97D595516F45794528a807ad8", "EURS"),
    ("0xD71eCFF9342A5Ced620049e616c5035F1dB98620", "sEUR"),
)


@pytest.mark.parametrize("token", [i[0] for i in tokens], ids=[i[1] for i in tokens])
@pytest.mark.parametrize("burner_balance", (True, False))
@pytest.mark.parametrize("caller_balance", (True, False))
def test_swap(MintableTestToken, SUSD, alice, receiver, burner, token, burner_balance, caller_balance):
    coin = MintableTestToken(token)
    amount = 10**coin.decimals()

    if caller_balance:
        coin._mint_for_testing(alice, amount, {'from': alice})
        coin.approve(burner, 2**256-1, {'from': alice})

    if burner_balance:
        coin._mint_for_testing(burner, amount, {'from': alice})

    burner.burn(coin, {'from': alice})

    if burner_balance or caller_balance:
        assert coin.balanceOf(alice) == 0
        assert coin.balanceOf(burner) == 0
        assert coin.balanceOf(receiver) == 0

        assert SUSD.balanceOf(alice) == 0
        assert SUSD.balanceOf(burner) > 0
        assert SUSD.balanceOf(receiver) == 0


def test_execute(SUSD, USDC, alice, burner, receiver):
    SUSD._mint_for_testing(burner, 10**18, {'from': alice})

    burner.execute({'from': alice})

    assert SUSD.balanceOf(alice) == 0
    assert SUSD.balanceOf(burner) == 0
    assert SUSD.balanceOf(receiver) == 0

    assert USDC.balanceOf(alice) == 0
    assert USDC.balanceOf(burner) == 0
    assert USDC.balanceOf(receiver) > 0


@pytest.mark.parametrize("token", [i[0] for i in tokens], ids=[i[1] for i in tokens])
def test_swap_and_execute(MintableTestToken, SUSD, USDC, alice, receiver, burner, token, chain):
    coin = MintableTestToken(token)
    amount = 10**coin.decimals()

    coin._mint_for_testing(alice, amount, {'from': alice})
    coin.approve(burner, 2**256-1, {'from': alice})

    burner.burn(coin, {'from': alice})

    chain.sleep(300)

    burner.execute({'from': alice})

    assert coin.balanceOf(alice) == 0
    assert coin.balanceOf(burner) == 0
    assert coin.balanceOf(receiver) == 0

    assert SUSD.balanceOf(alice) == 0
    assert SUSD.balanceOf(burner) == 0
    assert SUSD.balanceOf(receiver) == 0

    assert USDC.balanceOf(alice) == 0
    assert USDC.balanceOf(burner) == 0
    assert USDC.balanceOf(receiver) > 0
