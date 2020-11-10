import pytest


@pytest.fixture(scope="module")
def burner(MetaBurner, alice, receiver):
    yield MetaBurner.deploy(receiver, receiver, alice, alice, {'from': alice})


tokens = (
    ("0x056fd409e1d7a124bd7017459dfea2f387b6d5cd", "GUSD"),
    ("0xdf574c24545e5ffecb9a659c229253d4111d87e1", "HUSD"),
    ("0x1c48f86ae57291f7686349f12601910bd8d470bb", "USDK"),
    ("0x674C6Ad92Fd080e4004b2312b45f796a192D27a0", "USDN"),
    ("0x0E2EC54fC0B509F445631Bf4b91AB8168230C752", "LinkUSD"),
    ("0xe2f2a5C287993345a840Db3B0845fbC70f5935a5", "MUSD"),
    ("0x196f4727526eA7FB1e17b2071B3d8eAA38486988", "RSV"),
    ("0x5bc25f649fc4e26069ddf4cf4010f9f706c23831", "DUSD"),
)


@pytest.mark.parametrize("token", [i[0] for i in tokens], ids=[i[1] for i in tokens])
@pytest.mark.parametrize("burner_balance", (True, False))
@pytest.mark.parametrize("caller_balance", (True, False))
def test_swap(MintableTestToken, ThreeCRV, alice, receiver, burner, token, burner_balance, caller_balance):
    wrapped = MintableTestToken(token)
    amount = 10**wrapped.decimals()

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

        assert ThreeCRV.balanceOf(alice) == 0
        assert ThreeCRV.balanceOf(receiver) > 0
        assert ThreeCRV.balanceOf(burner) == 0
