import brownie


def pack_values(values):
    packed = b"".join(i.to_bytes(1, "big") for i in values)
    padded = packed + bytes(32 - len(values))
    return padded


def test_share_staking(web3, chain, accounts, ERC20, ERC20Staking, ERC20LP, CurvePool, PoolProxy, StakingBurner, LiquidityGauge, Minter, ERC20CRV, VotingEscrow, GaugeController, token):
    alice, bob, ve = accounts[:3]

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

    voting_escrow = VotingEscrow.deploy(
        token, 'Voting-escrowed CRV', 'veCRV', 'veCRV_0.99', {'from': alice})
    controller = GaugeController.deploy(token, voting_escrow, {'from': alice})
    minter = Minter.deploy(token, controller, {'from': alice})
    gauge = LiquidityGauge.deploy(lp, minter, alice, {'from': alice})
    burner = StakingBurner.deploy(ve, pool, proxy, gauge, {'from': alice})
    proxy.set_burner(usdn, burner)

    controller.add_type("simple", 10)
    controller.add_gauge(gauge, 0, 10)

    # first holder
    chain.sleep(86400)
    pool.add_liquidity([10 ** 18, 10 ** 18], 0, {'from': alice})
    chain.sleep(86400)
    assert usdn.balanceOf(pool) == 10 ** 18
    assert usdn.balanceOf(proxy) == 0
    assert usdn.balanceOf(alice) == 0
    lp.approve(gauge, 2**256-1, {'from': alice})
    chain.sleep(86400)
    gauge.deposit(lp.balanceOf(alice), {'from': alice})
    chain.sleep(86400)
    chain.sleep(86400)
    usdn.reward(10 ** 18)
    chain.sleep(86400)
    chain.sleep(86400)
    assert usdn.balanceOf(pool) == 2 * (10 ** 18)
    assert usdn.balanceOf(proxy) == 0
    gauge.user_checkpoint(alice)
    proxy.withdraw_admin_fees(pool, {'from': alice})
    assert usdn.balanceOf(pool) == 10 ** 18
    assert usdn.balanceOf(proxy) == 10 ** 18

    alice_burn = burner.claim_tokens(usdn)
    burner.burn_coin(usdn, {'from': alice})
    assert usdt.balanceOf(ve) == 1
    assert usdn.balanceOf(alice) == alice_burn
    assert usdn.balanceOf(proxy) == 10 ** 18 - alice_burn

    # reburn
    proxy.withdraw_admin_fees(pool, {'from': alice})
    with brownie.reverts("Already burned"):
        burner.burn_coin(usdn, {'from': alice})
    assert usdn.balanceOf(alice) == alice_burn
    assert usdn.balanceOf(proxy) == 10 ** 18 - alice_burn

    # equal holders
    usdt._mint_for_testing(10 ** 18, {'from': bob})
    usdn.approve(pool, 2**256-1, {'from': bob})
    usdn._mint_for_testing(10 ** 18, {'from': bob})
    usdt.approve(pool, 2**256-1, {'from': bob})
    assert usdt.balanceOf(bob) == 10 ** 18
    assert usdn.balanceOf(bob) == 10 ** 18

    chain.sleep(86400)
    pool.add_liquidity([10 ** 18, 10 ** 18], 100, {'from': bob})
    chain.sleep(86400)
    assert usdn.balanceOf(pool) == 2 * 10 ** 18
    assert usdn.balanceOf(proxy) == 10 ** 18 - alice_burn
    assert usdn.balanceOf(alice) == alice_burn
    assert usdn.balanceOf(bob) == 0
    lp.approve(gauge, 2**256-1, {'from': bob})
    chain.sleep(86400)
    gauge.deposit(lp.balanceOf(bob), {'from': bob})
    chain.sleep(86400)
    chain.sleep(86400)
    usdn.reward(10 ** 18)
    chain.sleep(86400)
    chain.sleep(86400)
    assert usdn.balanceOf(pool) == 3 * (10 ** 18)
    assert usdn.balanceOf(proxy) == 900000000000000001
    gauge.user_checkpoint(bob, {"from": bob})
    proxy.withdraw_admin_fees(pool, {'from': alice})

    assert usdn.balanceOf(pool) == 2000000000000000000
    assert usdn.balanceOf(proxy) == 1900000000000000001

    bob_burn = burner.claim_tokens(usdn, {'from': bob})
    burner.burn_coin(usdn, {'from': bob})
    assert usdn.balanceOf(bob) == bob_burn
