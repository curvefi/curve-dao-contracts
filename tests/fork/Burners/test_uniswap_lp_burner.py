import pytest

from abi.ERC20 import ERC20


@pytest.fixture(scope="module")
def burner(UniswapLPBurner, alice, receiver):
    yield UniswapLPBurner.deploy(receiver, receiver, alice, alice, {"from": alice})


UNISWAP_LP_TOKEN = "0xa478c2975ab1ea89e8196811f51a7b7ade33eb11"  # UNI-V2-DAI-ETH
SUSHISWAP_LP_TOKEN = "0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f"  # SLP-DAI-ETH


@pytest.mark.parametrize("token", [UNISWAP_LP_TOKEN, SUSHISWAP_LP_TOKEN])
def test_burn(MintableTestToken, DAI, WETH, alice, receiver, burner, token):
    coin = MintableTestToken.from_abi("testToken", token, abi=ERC20)
    amount = 10 ** coin.decimals()

    coin._mint_for_testing(alice, amount, {"from": alice})
    coin.approve(burner, 2 ** 256 - 1, {"from": alice})

    burner.burn(coin, {"from": alice})

    assert coin.balanceOf(alice) == 0
    assert coin.balanceOf(burner) == 0
    assert coin.balanceOf(receiver) == 0

    assert DAI.balanceOf(alice) == 0
    assert DAI.balanceOf(burner) == 0
    assert DAI.balanceOf(receiver) > 0

    assert WETH.balanceOf(alice) == 0
    assert WETH.balanceOf(burner) == 0
    assert WETH.balanceOf(receiver) > 0
