import pytest
from brownie import ETH_ADDRESS


@pytest.fixture(scope="module")
def burner(ETHBurner, alice, receiver):
    yield ETHBurner.deploy(receiver, receiver, alice, alice, {'from': alice})


tokens = (
    ("0x5e74C9036fb86BD7eCdcb084a0673EFc32eA31cb", "sETH"),
    ("0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84", "stETH"),
    ("0xE95A203B1a91a908F9B9CE46459d101078c2c3cb", "aETH"),
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


def test_swap_ether(MintableTestToken, SUSD, alice, receiver, burner):
    burner.burn(ETH_ADDRESS, {'from': alice, 'value': "1 ether"})

    assert alice.balance() == "99 ether"
    assert burner.balance() == 0
    assert receiver.balance() == 0

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
