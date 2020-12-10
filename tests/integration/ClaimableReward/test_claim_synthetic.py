import brownie


def test_claim(ERC20, ERC20LP, CurvePool, PoolProxy, VotingEscrow, GaugeController, Minter, LiquidityGauge, ClaimableReward, accounts, token, chain):
    neo, trinity, morpheus = accounts[:3]

    usdt = ERC20.deploy("Stable coin 1", "USDT", 18, {'from': neo})
    usdn = ERC20.deploy("Stable coin 2", "USDN", 18, {'from': neo})
    lp = ERC20LP.deploy("Curve LP token", "sCRV", 18, 0, {'from': neo})

    pool = CurvePool.deploy([usdt, usdn], lp, 100, 4 * 10 ** 6, {'from': neo})
    lp.set_minter(pool)

    proxy = PoolProxy.deploy(neo, neo, neo, {'from': neo})
    pool.commit_transfer_ownership(proxy, {'from': neo})
    pool.apply_transfer_ownership({'from': neo})

    usdt._mint_for_testing(10 ** 18)
    usdn.approve(pool, 2**256-1, {'from': neo})
    usdn._mint_for_testing(10 ** 18)
    usdt.approve(pool, 2**256-1, {'from': neo})
    usdt._mint_for_testing(10 ** 18, {'from': trinity})
    usdn.approve(pool, 2**256-1, {'from': trinity})
    usdn._mint_for_testing(10 ** 18, {'from': trinity})
    usdt.approve(pool, 2**256-1, {'from': trinity})
    usdt._mint_for_testing(10 ** 18, {'from': morpheus})
    usdn.approve(pool, 2**256-1, {'from': morpheus})
    usdn._mint_for_testing(10 ** 18, {'from': morpheus})
    usdt.approve(pool, 2**256-1, {'from': morpheus})

    voting_escrow = VotingEscrow.deploy(
        token, 'Voting-escrowed CRV', 'veCRV', 'veCRV_0.99', {'from': neo})
    controller = GaugeController.deploy(token, voting_escrow, {'from': neo})
    minter = Minter.deploy(token, controller, {'from': neo})
    gauge = LiquidityGauge.deploy(lp, minter, neo, {'from': neo})

    controller.add_type("simple", 10)
    controller.add_gauge(gauge, 0, 10)

    claimContract = ClaimableReward.deploy(gauge, {'from': neo})

    # first holder
    chain.sleep(86400)
    pool.add_liquidity([10 ** 18, 10 ** 18], 0, {'from': neo})
    pool.add_liquidity([10 ** 18, 10 ** 18], 0, {'from': trinity})
    pool.add_liquidity([10 ** 18, 10 ** 18], 0, {'from': morpheus})
    chain.sleep(86400)
    lp.approve(gauge, 2**256-1, {'from': neo})
    lp.approve(gauge, 2**256-1, {'from': trinity})
    lp.approve(gauge, 2**256-1, {'from': morpheus})
    chain.sleep(86400)
    gauge.deposit(lp.balanceOf(neo), {'from': neo})
    gauge.deposit(lp.balanceOf(trinity), {'from': trinity})
    gauge.deposit(lp.balanceOf(morpheus), {'from': morpheus})
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    # assert usdn.balanceOf(pool) == 10 ** 18
    # assert usdn.balanceOf(proxy) == 0
    # gauge.user_checkpoint(neo)
    # assert usdt.balanceOf(pool) == 10 ** 18
    # assert usdt.balanceOf(proxy) == 0
    gauge.user_checkpoint(neo)
    gauge.user_checkpoint(trinity, {'from': trinity})
    gauge.user_checkpoint(morpheus, {'from': morpheus})

    usdn._mint_for_testing(2 * 10 ** 18, {'from': neo})
    usdt._mint_for_testing(2 * 10 ** 18, {'from': neo})
    usdn.transfer(claimContract, 2 * 10 ** 18, {'from': neo})
    usdt.transfer(claimContract, 2 * 10 ** 18, {'from': neo})

    print(claimContract.claim_tokens(usdn))
    print(claimContract.claim_tokens(usdn, {'from': trinity}))
    print(claimContract.claim_tokens(usdn, {'from': morpheus}))

    assert False
