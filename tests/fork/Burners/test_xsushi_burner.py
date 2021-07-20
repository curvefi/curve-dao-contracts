import pytest

from abi.ERC20 import ERC20


@pytest.fixture(scope="module")
def burner(XSushiBurner, alice, receiver):
    yield XSushiBurner.deploy(receiver, receiver, alice, alice, {"from": alice})


XSUSHI = "0x8798249c2E607446EfB7Ad49eC89dD1865Ff4272"
SUSHI = "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2"


def test_burn_swap(MintableTestToken, DAI, WETH, alice, receiver, burner, token):
    xSushi = MintableTestToken.from_abi("xSushi", XSUSHI, abi=ERC20)
    sushi = MintableTestToken.from_abi("Sushi", SUSHI, abi=ERC20)
    amount = 10 ** xSushi.decimals()

    xSushi._mint_for_testing(alice, amount, {"from": alice})
    xSushi.approve(burner, 2 ** 256 - 1, {"from": alice})

    assert xSushi.balanceOf(alice) == amount
    assert xSushi.balanceOf(burner) == 0
    assert xSushi.balanceOf(receiver) == 0

    burner.burn(xSushi, {"from": alice})

    assert xSushi.balanceOf(alice) == 0
    assert xSushi.balanceOf(burner) == 0
    assert xSushi.balanceOf(receiver) == 0

    assert sushi.balanceOf(alice) == 0
    assert sushi.balanceOf(burner) == 0
    assert sushi.balanceOf(receiver) > 0
