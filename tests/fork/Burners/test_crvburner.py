import pytest
from brownie import ZERO_ADDRESS, Contract
from brownie_tokens import MintableForkToken

LP_TOKENS = [
    "0x4DEcE678ceceb27446b35C672dC7d61F30bAD69E",  # USDC/crvUSD
    "0x34d655069f4cac1547e4c8ca284ffff5ad4a8db0",  # TUSD/crvUSD
    "0x390f3595bca2df7d23783dfd126427cceb997bf4",  # USDT/crvUSD
    "0xca978a0528116dda3cba9acd3e68bc6191ca53d0",  # USDP/crvUSD
]


@pytest.fixture(scope="module")
def pool_proxy():
    yield Contract("0xeCb456EA5365865EbAb8a2661B0c503410e9B347")


@pytest.fixture(scope="module")
def crvusd():
    return MintableForkToken("0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E")


@pytest.fixture(scope="module")
def lp_tokens():
    return [Contract(token) for token in LP_TOKENS]


@pytest.fixture(scope="module")
def burner(crvUSDBurner, crvusd, pool_proxy, alice, receiver, lp_tokens):
    burner = crvUSDBurner.deploy(
        crvusd,  # crvUSD
        pool_proxy,  # pool_proxy
        alice,  # owner
        alice,  # emergency_owner
        {"from": alice},
    )
    coins = lp_tokens + [crvusd]
    pool_proxy.set_many_burners(
        coins + [ZERO_ADDRESS] * (20 - len(coins)),
        [burner] * len(coins) + [ZERO_ADDRESS] * (20 - len(coins)),
        {"from": pool_proxy.ownership_admin()}
    )
    return burner


@pytest.fixture(scope="module")
def prioritized(lp_tokens):
    return lp_tokens[: len(lp_tokens) // 2]


@pytest.fixture(scope="module")
def not_prioritized(prioritized, lp_tokens):
    return [token for token in lp_tokens if token not in prioritized]


@pytest.fixture(scope="module", autouse=True)
def setup(burner, prioritized, alice):
    burner.set_pools(
        prioritized,
        {"from": alice},
    )


@pytest.fixture(scope="module")
def get_coin(crvusd):
    def inner(lp):
        coin = lp.coins(0)
        if coin == crvusd.address:
            coin = lp.coins(1)
        return Contract(coin)
    return inner


def test_lp(prioritized, not_prioritized, get_coin, burner, crvusd, pool_proxy, alice):
    for lp in prioritized:
        amount = lp.balanceOf(pool_proxy)
        amount_crvUSD = [crvusd.balanceOf(pool_proxy), crvusd.balanceOf(burner)]

        coin = get_coin(lp)
        adjustment = 10 ** (18 - coin.decimals())
        amount_coin = [coin.balanceOf(pool_proxy) * adjustment, coin.balanceOf(burner) * adjustment]

        burner.burn(lp, {"from": pool_proxy})

        assert lp.balanceOf(pool_proxy) == 0
        assert lp.balanceOf(burner) == 0

        assert crvusd.balanceOf(pool_proxy) == amount_crvUSD[0]
        assert crvusd.balanceOf(burner) == amount_crvUSD[1]

        assert coin.balanceOf(pool_proxy) * adjustment == pytest.approx(
            amount_coin[0] + amount, abs=amount * .01
        )
        assert coin.balanceOf(burner) * adjustment == amount_coin[1]

    for lp in not_prioritized:
        amount = lp.balanceOf(pool_proxy)
        amount_crvUSD = [crvusd.balanceOf(pool_proxy), crvusd.balanceOf(burner)]

        coin = get_coin(lp)
        amount_coin = [coin.balanceOf(pool_proxy), coin.balanceOf(burner)]

        burner.burn(lp, {"from": pool_proxy})

        assert lp.balanceOf(pool_proxy) == 0
        assert lp.balanceOf(burner) == 0

        assert crvusd.balanceOf(pool_proxy) == amount_crvUSD[0]
        assert int(crvusd.balanceOf(burner)) == pytest.approx(
            amount_crvUSD[1] + amount, abs=amount * .05
        )

        assert coin.balanceOf(pool_proxy) == amount_coin[0]
        assert coin.balanceOf(burner) == amount_coin[1]


def test_crvusd(prioritized, burner, crvusd, get_coin, pool_proxy, alice, chain):
    chain_initial = chain.height
    for pool in prioritized:
        # Move price
        coin = MintableForkToken(get_coin(pool).address)
        amount_coin = coin.balanceOf(pool) // 2
        coin._mint_for_testing(alice, amount_coin, {"from": alice})
        coin.approve(pool, amount_coin, {"from": alice})
        pool.exchange(0, 1, amount_coin, 0, {"from": alice})

        adjustment = 10 ** (18 - coin.decimals())
        initial_amounts = [coin.balanceOf(pool_proxy) * adjustment, crvusd.balanceOf(pool_proxy)]

        burner.burn(crvusd, {"from": pool_proxy})

        assert crvusd.balanceOf(pool_proxy) == 0
        assert crvusd.balanceOf(burner) == 0

        assert coin.balanceOf(pool_proxy) * adjustment > sum(initial_amounts)
        assert coin.balanceOf(burner) == 0

        chain.undo(chain.height - chain_initial)
