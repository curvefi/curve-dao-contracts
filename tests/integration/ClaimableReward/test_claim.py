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
    assert usdt.balanceOf(neo) == 10 ** 18
    assert usdn.balanceOf(neo) == 10 ** 18

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
    chain.sleep(86400)
    assert usdn.balanceOf(pool) == 10 ** 18
    assert usdn.balanceOf(proxy) == 0
    assert usdn.balanceOf(neo) == 0
    lp.approve(gauge, 2**256-1, {'from': neo})
    chain.sleep(86400)
    gauge.deposit(lp.balanceOf(neo), {'from': neo})
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    assert usdn.balanceOf(pool) == 10 ** 18
    assert usdn.balanceOf(proxy) == 0
    gauge.user_checkpoint(neo)
    assert usdt.balanceOf(pool) == 10 ** 18
    assert usdt.balanceOf(proxy) == 0

    # setup
    usdn._mint_for_testing(2 * 10 ** 18, {'from': neo})
    usdt._mint_for_testing(2 * 10 ** 18, {'from': neo})
    usdn.transfer(claimContract, 2 * 10 ** 18, {'from': neo})
    usdt.transfer(claimContract, 2 * 10 ** 18, {'from': neo})
    assert usdn.balanceOf(claimContract) == 2 * 10 ** 18
    assert usdt.balanceOf(claimContract) == 2 * 10 ** 18

    # check share reward for first holder
    assert claimContract.claim_tokens(usdn) == 1999999999999999999
    assert claimContract.claim_tokens(usdt) == 1999999999999999999
    assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdn, {'from': morpheus}) == 0
    assert claimContract.claim_tokens(usdt, {'from': morpheus}) == 0

    claimContract.claim(usdn)
    claimContract.claim(usdt)
    assert usdn.balanceOf(neo) == 1999999999999999999
    assert usdt.balanceOf(neo) == 1999999999999999999
    assert claimContract.claim_tokens(usdn) == 0
    assert claimContract.claim_tokens(usdt) == 0
    assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdn, {'from': morpheus}) == 0
    assert claimContract.claim_tokens(usdt, {'from': morpheus}) == 0

    with brownie.reverts("already claimed"):
        claimContract.claim(usdn)
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt)

    # share for all holders
    usdt._mint_for_testing(10 ** 18, {'from': trinity})
    usdn.approve(pool, 2**256-1, {'from': trinity})
    usdn._mint_for_testing(10 ** 18, {'from': trinity})
    usdt.approve(pool, 2**256-1, {'from': trinity})
    usdt._mint_for_testing(10 ** 18, {'from': morpheus})
    usdn.approve(pool, 2**256-1, {'from': morpheus})
    usdn._mint_for_testing(10 ** 18, {'from': morpheus})
    usdt.approve(pool, 2**256-1, {'from': morpheus})

    pool.add_liquidity([10 ** 18, 10 ** 18], 0, {'from': trinity})
    lp.approve(gauge, 2**256-1, {'from': trinity})
    pool.add_liquidity([10 ** 18, 10 ** 18], 0, {'from': morpheus})
    lp.approve(gauge, 2**256-1, {'from': morpheus})
    gauge.deposit(lp.balanceOf(trinity), {'from': trinity})
    gauge.deposit(lp.balanceOf(morpheus), {'from': morpheus})
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    gauge.user_checkpoint(neo)
    gauge.user_checkpoint(trinity, {'from': trinity})
    gauge.user_checkpoint(morpheus, {'from': morpheus})

    assert claimContract.claim_tokens(usdn) == 0
    assert claimContract.claim_tokens(usdt) == 0
    assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdn, {'from': morpheus}) == 0
    assert claimContract.claim_tokens(usdt, {'from': morpheus}) == 0

    usdn._mint_for_testing(10 * 10 ** 18, {'from': neo})
    usdt._mint_for_testing(10 * 10 ** 18, {'from': neo})
    usdn.transfer(claimContract, 10 * 10 ** 18, {'from': neo})
    usdt.transfer(claimContract, 10 * 10 ** 18, {'from': neo})
    assert usdn.balanceOf(claimContract) == 10000000000000000001
    assert usdt.balanceOf(claimContract) == 10000000000000000001

    assert claimContract.claim_tokens(usdn) == 3333333333333333333
    assert claimContract.claim_tokens(usdt) == 3333333333333333333
    assert claimContract.claim_tokens(
        usdn, {'from': trinity}) == 2555463443943323471
    assert claimContract.claim_tokens(
        usdt, {'from': trinity}) == 2555463443943323471
    assert claimContract.claim_tokens(
        usdn, {'from': morpheus}) == 3333333333333333333
    assert claimContract.claim_tokens(
        usdt, {'from': morpheus}) == 3333333333333333333

    # # claimContract.claim(usdn, {'from': trinity})
    # # claimContract.claim(usdn, {'from': morpheus})
    # # claimContract.claim(usdt, {'from': trinity})
    # # claimContract.claim(usdt, {'from': morpheus})
    # # assert claimContract.claim_tokens(usdn, {'from': neo}) == 0
    # # assert claimContract.claim_tokens(usdt, {'from': neo}) == 0
    # # assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    # # assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    # # assert claimContract.claim_tokens(usdn, {'from': morpheus}) == 0
    # # assert claimContract.claim_tokens(usdt, {'from': morpheus}) == 0

    # # assert usdn.balanceOf(neo) + usdn.balanceOf(trinity) + \
    # #     usdn.balanceOf(morpheus) < 2 * 10 ** 18
    # # assert usdt.balanceOf(neo) + usdt.balanceOf(trinity) + \
    # #     usdt.balanceOf(morpheus) < 2 * 10 ** 18

    # # usdn._mint_for_testing(2 * 10 ** 18, {'from': neo})
    # # usdt._mint_for_testing(2 * 10 ** 18, {'from': neo})
    # # usdn.transfer(claimContract, 2 * 10 ** 18, {'from': neo})
    # # usdt.transfer(claimContract, 2 * 10 ** 18, {'from': neo})
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # gauge.user_checkpoint(neo)
    # # gauge.user_checkpoint(trinity, {'from': trinity})
    # # gauge.user_checkpoint(morpheus, {'from': morpheus})

    # # # assert claimContract.claim_tokens(usdn) == 0
    # # # assert claimContract.claim_tokens(usdt) == 0

    # # assert claimContract.claim_tokens(
    # #     usdn, {'from': morpheus}) == 0

    # # # assert abs(claimContract.claim_tokens(
    # # # usdn, {'from': trinity}) - 0.1178 * 10**18) < 10 ** 15
    # # # assert abs(claimContract.claim_tokens(
    # # # usdt, {'from': trinity}) - 0.1178 * 10**18) < 10 ** 15
    # # assert abs(claimContract.claim_tokens(
    # #     usdn, {'from': morpheus}) - 0.1178 * 10**18) < 10 ** 15
    # # assert abs(claimContract.claim_tokens(
    # #     usdt, {'from': morpheus}) - 0.1178 * 10**18) < 10 ** 15
