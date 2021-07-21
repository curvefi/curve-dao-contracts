import brownie
import pytest

from abi.ERC20 import ERC20


@pytest.fixture(scope="module")
def burner(UniswapBurner, alice, receiver):
    yield UniswapBurner.deploy(receiver, receiver, alice, alice, {"from": alice})


BBADGER = "0x19d97d8fa813ee2f51ad4b4e04ea08baf4dffc28"


def test_burn(MintableTestToken, USDC, alice, receiver, burner):
    bbadger = MintableTestToken.from_abi("bbadger", BBADGER, abi=ERC20)

    amount = 10 ** bbadger.decimals()

    bbadger._mint_for_testing(alice, amount, {"from": alice})
    bbadger.approve(burner, 2 ** 256 - 1, {"from": alice})

    burner.burn(bbadger, {"from": alice})

    assert bbadger.balanceOf(alice) == 0
    assert bbadger.balanceOf(burner) == 0
    assert bbadger.balanceOf(receiver) == 0

    assert USDC.balanceOf(alice) == 0
    assert USDC.balanceOf(burner) == 0
    assert USDC.balanceOf(receiver) > 0


def test_burn_unburnable(MintableTestToken, USDC, alice, receiver, burner):
    # CMC Rank 500 coin, not available in either sushi or uniswap
    turtle = MintableTestToken.from_abi(
        "turtle", "0xf3afdc2525568ffe743801c8c54bdea1704c9adb", abi=ERC20
    )

    amount = 10 ** turtle.decimals()

    turtle._mint_for_testing(alice, amount, {"from": alice})
    turtle.approve(burner, 2 ** 256 - 1, {"from": alice})
    with brownie.reverts("neither Uniswap nor Sushiswap has liquidity pool for this token"):
        burner.burn(turtle, {"from": alice})
