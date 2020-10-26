def pack_values(values):
    packed = b"".join(i.to_bytes(1, "big") for i in values)
    padded = packed + bytes(32 - len(values))
    return padded


def test_share_staking(web3, chain, accounts, ERC20, ERC20Staking, ERC20LP, CurvePool, PoolProxy, StakingBurner, LiquidityGauge, Minter, ERC20CRV, VotingEscrow, GaugeController):
    alice, bob = accounts[:2]

    usdt = ERC20.deploy("Stable coin", "USDT", 18, {'from': alice})
    usdn = ERC20Staking.deploy("Staking coin", "USDN", 18, {'from': alice})
    lp = ERC20LP.deploy("Curve share LP token", "shareCrv", 18,
                        0, {'from': alice})

    pool = CurvePool.deploy(
        [usdt, usdn], lp, 100, 4 * 10 ** 6, {'from': alice}
    )
    lp.set_minter(pool)

    proxy = PoolProxy.deploy(
        "0x0000000000000000000000000000000000000000", alice, alice, alice, {'from': alice})
    pool.commit_transfer_ownership(proxy, {'from': alice})
    pool.apply_transfer_ownership({'from': alice})

    usdt._mint_for_testing(10 ** 18)
    usdn.approve(pool, 2**256-1, {'from': alice})
    usdn._mint_for_testing(10 ** 18)
    usdt.approve(pool, 2**256-1, {'from': alice})
    assert usdt.balanceOf(alice) == 10 ** 18
    assert usdn.balanceOf(alice) == 10 ** 18

    crv = ERC20CRV.deploy("Curve DAO Token", "CRV", 18, {'from': alice})
    voting_escrow = VotingEscrow.deploy(
        crv, 'Voting-escrowed CRV', 'veCRV', 'veCRV_0.99', {'from': alice})
    controller = GaugeController.deploy(crv, voting_escrow, {'from': alice})
    minter = Minter.deploy(crv, controller, {'from': alice})
    gauge = LiquidityGauge.deploy(lp, minter, alice, {'from': alice})
    burner = StakingBurner.deploy(proxy, gauge, {'from': alice})

    pool.add_liquidity([10 ** 18, 10 ** 18], 0, {'from': alice})
    lp.approve(gauge, 2**256-1, {'from': alice})
    proxy.set_burner(usdn, burner)
    chain.sleep(1000)
    chain.mine(1000)
    gauge.deposit(lp.balanceOf(alice), {'from': alice})

    usdn._set_interest('2.0')
    proxy.withdraw_admin_fees(pool)
    chain.sleep(1000)
    chain.mine(1000)
    print(gauge.user_checkpoint(alice))
    chain.sleep(1000)
    chain.mine(1000)

    print('balance_proxy', usdn.balanceOf(proxy))
    print('integrate_fraction', gauge.integrate_fraction(alice))

    print(proxy.burn_coin(usdn, {'from': alice}))
    assert usdn.balanceOf(alice) == 1000/2/2  # wrong value
