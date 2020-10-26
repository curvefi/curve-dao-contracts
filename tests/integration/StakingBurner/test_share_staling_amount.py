def pack_values(values):
    packed = b"".join(i.to_bytes(1, "big") for i in values)
    padded = packed + bytes(32 - len(values))
    return padded


def test_share_staking(accounts, ERC20, ERC20LP, CurvePool, Registry):
    alice, bob = accounts[:2]

    coin_a = ERC20.deploy("Stable coin", "USDT", 18, {'from': alice})
    coin_b = ERC20.deploy("Staking coin", "USDN", 18, {'from': alice})
    lp = ERC20LP.deploy("Curve share LP token", "shareCrv", 18,
                        1000 * 10 ** 18, {'from': alice})

    pool = CurvePool.deploy(
        [coin_a, coin_b], lp, 100, 4 * 10 ** 6, {'from': alice}
    )
    lp.set_minter(pool)

    registry = Registry.deploy(
        ["0x0000000000000000000000000000000000000000"] * 4, {'from': alice})
    registry.add_pool(
        pool, 2, lp,
        "0x0000000000000000000000000000000000000000", "0x00",
        pack_values([18, 18]), pack_values([18, 18]),
        {'from': alice})

    # coin_a._mint_for_testing(10 ** 18)
    # coin_b._mint_for_testing(10 ** 18)
    # pool.add_liquidity([10 ** 18, 10 ** 18], 1, {'from': accounts[0]})

    # pool_proxy.burn_coin(coin_a, {'from': accounts[0]})
    # pool_proxy.burn_coin(coin_a, {'from': accounts[1]})

    # assert coin_a.balanceOf(accounts[0]) == 1000/2/2  # wrong value
    # assert coin_a.balanceOf(accounts[1]) == 1000/2/2 # wrong value

    # pool_proxy.set_burner(coin_a, staking_burner)
    # liquidity_gauge.deposit(10 ** 18, {'from': accounts[0]})
    # liquidity_gauge.deposit(10 ** 18, {'from': accounts[1]})
    # assert liquidity_gauge.balanceOf(accounts[0]) == 10 ** 18
    # assert liquidity_gauge.balanceOf(accounts[0]) == 10 ** 18
