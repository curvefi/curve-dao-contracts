import brownie
import pytest

from abi.ERC20 import ERC20


@pytest.fixture(scope="module")
def burner(YearnVaultBurner, alice, receiver):
    yield YearnVaultBurner.deploy(receiver, receiver, alice, alice, {"from": alice})


YVCrvSETH = "0x986b4AFF588a109c09B50A03f42E4110E29D353F"
CrvSETH = "0xa3d87fffce63b53e0d54faa1cc983b7eb0b74a9c"
YVCrvSTETH = "0xdCD90C7f6324cfa40d7169ef80b12031770B4325"
CrvSTETH = "0x06325440d014e39736583c165c2963ba99faf14e"

burnable_coins = {
    YVCrvSETH: CrvSETH,
    YVCrvSTETH: CrvSTETH,
}


@pytest.mark.parametrize("token,result_token", [(k, v) for k, v in burnable_coins.items()])
def test_burn(MintableTestToken, alice, receiver, burner, token, result_token):
    token = MintableTestToken.from_abi("test", token, abi=ERC20)  # Yearn Vault Curve: sETH
    result_token = MintableTestToken.from_abi("result_token", result_token, abi=ERC20)
    amount = 10 ** token.decimals()

    token._mint_for_testing(alice, amount, {"from": alice})
    token.approve(burner, 2 ** 256 - 1, {"from": alice})

    assert token.balanceOf(alice) == amount
    assert token.balanceOf(burner) == 0
    assert token.balanceOf(receiver) == 0

    burner.burn(token, {"from": alice})

    assert token.balanceOf(alice) == 0
    assert token.balanceOf(burner) == 0
    assert token.balanceOf(receiver) == 0

    assert result_token.balanceOf(alice) == 0
    assert result_token.balanceOf(burner) == 0
    assert result_token.balanceOf(receiver) > 0


def test_burn_invalid_token(MintableTestToken, alice, burner, receiver):
    unapproved_token_address = (
        "0xBfedbcbe27171C418CDabC2477042554b1904857"  # yVault:Curve rETH Pool
    )
    result_token_address = "0x53a901d48795c58f485cbb38df08fa96a24669d5"  # Curve rEth LP
    unapproved_token = MintableTestToken.from_abi("yVCRVrETH", unapproved_token_address, abi=ERC20)
    result_token = MintableTestToken.from_abi("CRVrETH", result_token_address, abi=ERC20)
    amount = 10 ** unapproved_token.decimals()
    unapproved_token._mint_for_testing(alice, amount, {"from": alice})
    # revert when token is not added to burnable_tokens
    with brownie.reverts("token not burnable"):
        burner.burn(unapproved_token_address, {"from": alice})

    assert unapproved_token.balanceOf(alice) == amount
    assert unapproved_token.balanceOf(burner) == 0
    assert unapproved_token.balanceOf(receiver) == 0

    # add token to burnable_tokens and burn
    burner.add_burnable_coin(unapproved_token_address, {"from": alice})
    unapproved_token.approve(burner, 2 ** 256 - 1, {"from": alice})
    burner.burn(unapproved_token_address, {"from": alice})

    assert unapproved_token.balanceOf(alice) == 0
    assert unapproved_token.balanceOf(burner) == 0
    assert unapproved_token.balanceOf(receiver) == 0

    assert result_token.balanceOf(alice) == 0
    assert result_token.balanceOf(burner) == 0
    assert result_token.balanceOf(receiver) > 0
