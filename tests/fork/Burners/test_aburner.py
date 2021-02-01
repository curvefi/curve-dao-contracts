import pytest
from brownie import Contract


@pytest.fixture(scope="module")
def burner(ABurner, alice, receiver):
    yield ABurner.deploy(receiver, receiver, alice, alice, {"from": alice})


ctokens = (
    ("0x028171bCA77440897B824Ca71D1c56caC55b68A3", "aDAI"),
    ("0xBcca60bB61934080951369a648Fb03DF4F96263C", "aUSDC"),
    ("0x3Ed3B47Dd13EC9a98b44e6204A523E766B225811", "aUSDT"),
)


@pytest.mark.parametrize("token", [i[0] for i in ctokens], ids=[i[1] for i in ctokens])
@pytest.mark.parametrize("burner_balance", (True, False))
@pytest.mark.parametrize("caller_balance", (True, False))
def test_ctoken_unwrap(
    MintableTestToken, alice, receiver, burner, token, burner_balance, caller_balance
):
    wrapped = MintableTestToken(token)
    amount = 10 ** wrapped.decimals()
    underlying = Contract(wrapped.UNDERLYING_ASSET_ADDRESS())

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
