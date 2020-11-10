import pytest


@pytest.fixture(scope="module")
def btc_burner(BTCBurner, alice, receiver):
    yield BTCBurner.deploy(receiver, receiver, alice, alice, {'from': alice})


@pytest.fixture(scope="module")
def lp_burner(LPBurner, alice, receiver):
    yield LPBurner.deploy(receiver, alice, alice, {'from': alice})


tokens = (
    ("0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3", "sbtcCRV"),
)


@pytest.mark.parametrize("token", [i[0] for i in tokens], ids=[i[1] for i in tokens])
@pytest.mark.parametrize("burner_balance", (True, False))
@pytest.mark.parametrize("caller_balance", (True, False))
def test_swap(MintableTestToken, SBTC, alice, receiver, lp_burner, btc_burner, token, burner_balance, caller_balance):
    coin = MintableTestToken(token)
    amount = 10**coin.decimals()

    lp_burner.set_swap_data(token, SBTC, btc_burner)

    if caller_balance:
    coin._mint_for_testing(alice, amount, {'from': alice})
    coin.approve(lp_burner, 2**256-1, {'from': alice})

    if burner_balance:
        coin._mint_for_testing(lp_burner, amount, {'from': alice})

    lp_burner.burn(coin, {'from': alice})

    if burner_balance or caller_balance:
        assert coin.balanceOf(alice) == 0
        assert coin.balanceOf(lp_burner) == 0
        assert coin.balanceOf(btc_burner) == 0
        assert coin.balanceOf(receiver) == 0

        assert SBTC.balanceOf(alice) == 0
        assert SBTC.balanceOf(lp_burner) == 0
        assert SBTC.balanceOf(btc_burner) > 0
        assert SBTC.balanceOf(receiver) == 0
