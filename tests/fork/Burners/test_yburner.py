import pytest
from brownie import Contract


@pytest.fixture(scope="module")
def burner(YBurner, alice, receiver):
    yield YBurner.deploy(receiver, receiver, alice, alice, {'from': alice})


y_unwrap = (
    ("0xC2cB1040220768554cf699b0d863A3cd4324ce32", "y/yDAI"),
    ("0x26EA744E5B887E5205727f55dFBE8685e3b21951", "y/yUSDC"),
    ("0xE6354ed5bC4b393a5Aad09f21c46E101e692d447", "y/yUSDT"),
    ("0x16de59092dAE5CcF4A1E6439D611fd0653f0Bd01", "busd/yDAI"),
    ("0xd6aD7a6750A7593E092a9B218d66C0A814a3436e", "busd/yUSDC"),
    ("0x83f798e925BcD4017Eb265844FDDAbb448f1707D", "busd/yUSDT"),
    ("0x99d1Fa417f94dcD62BfE781a1213c092a47041Bc", "pax/yDAI"),
    ("0x9777d7E2b60bB01759D0E2f8be2095df444cb07E", "pax/yUSDC"),
    ("0x1bE5d71F2dA660BFdee8012dDc58D024448A0A59", "pax/yUSDT"),
)
y_swap = (
    ("0x04bC0Ab673d88aE9dbC9DA2380cB6B79C4BCa9aE", "yTUSD"),
    ("0x73a052500105205d34Daf004eAb301916DA8190f", "yBUSD"),
)


@pytest.mark.parametrize("token", [i[0] for i in y_unwrap], ids=[i[1] for i in y_unwrap])
@pytest.mark.parametrize("burner_balance", (True, False))
@pytest.mark.parametrize("caller_balance", (True, False))
def test_unwrap(MintableTestToken, alice, receiver, burner, token, burner_balance, caller_balance):
    wrapped = MintableTestToken(token)
    amount = 10**wrapped.decimals()
    underlying = Contract(wrapped.token())

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


@pytest.mark.parametrize("token", [i[0] for i in y_swap], ids=[i[1] for i in y_swap])
@pytest.mark.parametrize("burner_balance", (True, False))
@pytest.mark.parametrize("caller_balance", (True, False))
def test_swap_and_unwrap(MintableTestToken, USDC, alice, receiver, burner, token, burner_balance, caller_balance):
    wrapped = MintableTestToken(token)
    amount = 10**wrapped.decimals()
    underlying = Contract(wrapped.token())

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
        assert underlying.balanceOf(receiver) == 0
        assert underlying.balanceOf(burner) == 0

        assert USDC.balanceOf(alice) == 0
        assert USDC.balanceOf(receiver) > 0
        assert USDC.balanceOf(burner) == 0
