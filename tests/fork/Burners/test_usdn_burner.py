import pytest


@pytest.fixture(scope="module")
def burner(USDNBurner, alice, receiver, pool_proxy, swap):
    contract = USDNBurner.deploy(pool_proxy, receiver, receiver, alice, alice, {"from": alice})
    pool_proxy.set_donate_approval(swap, contract, True, {"from": alice})

    yield contract


@pytest.fixture(scope="module")
def swap(Contract):
    yield Contract("0x0f9cb53Ebe405d49A0bbdBD291A65Ff571bC83e1")


@pytest.fixture(scope="module")
def pool_proxy(PoolProxy, chain, alice, swap):
    contract = PoolProxy.deploy(alice, alice, alice, {"from": alice})
    swap.commit_transfer_ownership(contract, {"from": swap.owner()})
    chain.sleep(86400 * 3)
    swap.apply_transfer_ownership({"from": swap.owner()})

    yield contract


@pytest.fixture(scope="module")
def USDN(MintableTestToken):
    yield MintableTestToken("0x674C6Ad92Fd080e4004b2312b45f796a192D27a0")


@pytest.mark.parametrize("burner_balance", (True, False))
@pytest.mark.parametrize("caller_balance", (True, False))
def test_swap(
    USDN, ThreeCRV, alice, receiver, burner, burner_balance, caller_balance, swap, pool_proxy,
):
    amount = 0

    if caller_balance:
        amount += 10 ** 18
        USDN._mint_for_testing(alice, 10 ** 18, {"from": alice})
        USDN.approve(burner, 2 ** 256 - 1, {"from": alice})

    if burner_balance:
        amount += 10 ** 18
        USDN._mint_for_testing(burner, 10 ** 18, {"from": alice})

    swap_balance = swap.balances(0)

    burner.burn(USDN, {"from": alice})

    if burner_balance or caller_balance:
        assert USDN.balanceOf(alice) == 0
        assert USDN.balanceOf(receiver) == 0
        assert USDN.balanceOf(burner) == 0

        assert ThreeCRV.balanceOf(alice) == 0
        assert ThreeCRV.balanceOf(receiver) > 0
        assert ThreeCRV.balanceOf(burner) == 0

        assert swap.balances(0) == swap_balance + amount
        assert USDN.balanceOf(pool_proxy) > 0
