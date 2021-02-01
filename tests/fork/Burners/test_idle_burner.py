import pytest
from brownie import Contract


@pytest.fixture(scope="module")
def burner(IdleBurner, alice, receiver):
    yield IdleBurner.deploy(receiver, receiver, alice, alice, {"from": alice})


ctokens = (
    ("0x3fe7940616e5bc47b0775a0dccf6237893353bb4", "idleDAI"),
    ("0x5274891bEC421B39D23760c04A6755eCB444797C", "idleUSDC"),
    ("0xF34842d05A1c888Ca02769A633DF37177415C2f8", "idleUSDT"),
)


@pytest.mark.parametrize("token", [i[0] for i in ctokens], ids=[i[1] for i in ctokens])
@pytest.mark.parametrize("burner_balance", (True, False))
@pytest.mark.parametrize("caller_balance", (True, False))
def test_ctoken_unwrap(
    MintableTestToken, alice, receiver, burner, token, burner_balance, caller_balance
):
    wrapped = MintableTestToken(token)
    amount = 10 ** wrapped.decimals()
    underlying = Contract(wrapped.token())

    if caller_balance:
        wrapped._mint_for_testing(alice, amount, {"from": alice})
        wrapped.approve(burner, 2 ** 256 - 1, {"from": alice})

    if burner_balance:
        wrapped._mint_for_testing(burner, amount, {"from": alice})

    burner.burn(wrapped, {"from": alice})

    if burner_balance or caller_balance:
        assert wrapped.balanceOf(alice) == 0
        assert wrapped.balanceOf(receiver) == 0
        assert wrapped.balanceOf(burner) == 0

        assert underlying.balanceOf(alice) == 0
        assert underlying.balanceOf(receiver) > 0
        assert underlying.balanceOf(burner) == 0
