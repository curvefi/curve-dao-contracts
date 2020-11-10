import pytest
from brownie import Contract


@pytest.fixture(scope="module")
def burner(CBurner, alice, receiver):
    yield CBurner.deploy(receiver, receiver, alice, alice, {'from': alice})


ctokens = (
    ("0x39aa39c021dfbae8fac545936693ac917d5e7563", "cDAI"),
    ("0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643", "cUSDC"),
)


@pytest.mark.parametrize("token", [i[0] for i in ctokens], ids=[i[1] for i in ctokens])
@pytest.mark.parametrize("burner_balance", (True, False))
@pytest.mark.parametrize("caller_balance", (True, False))
def test_ctoken_unwrap(MintableTestToken, alice, receiver, burner, token, burner_balance, caller_balance):
    wrapped = MintableTestToken(token)
    amount = 10**wrapped.decimals()
    underlying = Contract(wrapped.underlying())

    if caller_balance:
        wrapped._mint_for_testing(alice, amount, {'from': alice})
        wrapped.approve(burner, 2**256-1, {'from': alice})

    if burner_balance:
        wrapped._mint_for_testing(burner, amount, {'from': alice})

    burner.burn(wrapped, {'from': alice})

    if burner_balance or caller_balance:
        assert wrapped.balanceOf(alice) == 0
        assert wrapped.balanceOf(receiver) == 0
        assert wrapped.balanceOf(burner) == 0

        assert underlying.balanceOf(alice) == 0
        assert underlying.balanceOf(receiver) > 0
        assert underlying.balanceOf(burner) == 0
