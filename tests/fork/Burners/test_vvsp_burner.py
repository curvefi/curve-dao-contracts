import brownie
import pytest

from abi.ERC20 import ERC20


@pytest.fixture(scope="module")
def burner(VvspBurner, alice, receiver):
    yield VvspBurner.deploy(receiver, receiver, alice, alice, {"from": alice})


VVSP = "0xba4cfe5741b357fa371b506e5db0774abfecf8fc"
VSP = "0x1b40183EFB4Dd766f11bDa7A7c3AD8982e998421"


def test_burn(MintableTestToken, alice, receiver, burner):
    vvsp = MintableTestToken.from_abi("VVSP", VVSP, abi=ERC20)
    vsp = MintableTestToken.from_abi("VSP", VSP, abi=ERC20)
    amount = 10 ** vvsp.decimals()

    vvsp._mint_for_testing(alice, amount, {"from": alice})
    vvsp.approve(burner, 2 ** 256 - 1, {"from": alice})

    assert vvsp.balanceOf(alice) == amount
    assert vvsp.balanceOf(burner) == 0
    assert vvsp.balanceOf(receiver) == 0

    burner.burn(vvsp, {"from": alice})

    assert vvsp.balanceOf(alice) == 0
    assert vvsp.balanceOf(burner) == 0
    assert vvsp.balanceOf(receiver) == 0

    assert vsp.balanceOf(alice) == 0
    assert vsp.balanceOf(burner) == 0
    assert vsp.balanceOf(receiver) > 0


def test_burn_invalid_token(MintableTestToken, alice, burner):
    vsp = MintableTestToken.from_abi("VSP", VSP, abi=ERC20)
    with brownie.reverts("only allows burning vvsp"):
        burner.burn(vsp, {"from": alice})
