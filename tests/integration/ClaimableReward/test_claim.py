import brownie

DECIMALS = 10 ** 18


def test_claim(ERC20, ERC20LP, CurvePool, PoolProxy, VotingEscrow, GaugeController, Minter, LiquidityGauge, ClaimableReward, accounts, token, chain):
    # init accounts
    neo, trinity, morpheus = accounts[:3]

    # init contracts
    usdt = ERC20.deploy("Stable coin 1", "USDT", 18, {'from': neo})
    usdn = ERC20.deploy("Stable coin 2", "USDN", 18, {'from': neo})
    lp = ERC20LP.deploy("Curve LP token", "sCRV", 18, 0, {'from': neo})

    pool = CurvePool.deploy([usdt, usdn], lp, 100, 4 * 10 ** 6, {'from': neo})
    lp.set_minter(pool)

    proxy = PoolProxy.deploy(neo, neo, neo, {'from': neo})
    pool.commit_transfer_ownership(proxy, {'from': neo})
    pool.apply_transfer_ownership({'from': neo})

    usdt._mint_for_testing(1 * DECIMALS)
    usdn.approve(pool, 2**256-1, {'from': neo})
    usdn._mint_for_testing(1 * DECIMALS)
    usdt.approve(pool, 2**256-1, {'from': neo})
    assert usdt.balanceOf(neo) == 1 * DECIMALS
    assert usdn.balanceOf(neo) == 1 * DECIMALS

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
    pool.add_liquidity([1 * DECIMALS, 1 * DECIMALS], 0, {'from': neo})
    chain.sleep(86400)
    assert usdn.balanceOf(pool) == 1 * DECIMALS
    assert usdn.balanceOf(proxy) == 0
    assert usdn.balanceOf(neo) == 0
    lp.approve(gauge, 2**256-1, {'from': neo})
    chain.sleep(86400)
    gauge.deposit(lp.balanceOf(neo), {'from': neo})
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    assert usdn.balanceOf(pool) == 1 * DECIMALS
    assert usdn.balanceOf(proxy) == 0
    gauge.user_checkpoint(neo)
    assert usdt.balanceOf(pool) == 1 * DECIMALS
    assert usdt.balanceOf(proxy) == 0

    # fill claimContract with money
    usdn._mint_for_testing(2 * DECIMALS, {'from': claimContract})
    usdt._mint_for_testing(2 * DECIMALS, {'from': claimContract})
    assert usdn.balanceOf(claimContract) == 2 * DECIMALS
    assert usdt.balanceOf(claimContract) == 2 * DECIMALS

    # check share reward for first holder
    assert abs(claimContract.claim_tokens(usdn) - 2 * DECIMALS) <= 10
    assert abs(claimContract.claim_tokens(usdt) - 2 * DECIMALS) <= 10
    assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdn, {'from': morpheus}) == 0
    assert claimContract.claim_tokens(usdt, {'from': morpheus}) == 0

    # claim reward
    claimContract.claim(usdn)
    claimContract.claim(usdt)
    assert abs(usdn.balanceOf(neo) - 2 * DECIMALS) <= 10
    assert abs(usdt.balanceOf(neo) - 2 * DECIMALS) <= 10
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

    # share money for trinity and morpheus
    usdt._mint_for_testing(1 * DECIMALS, {'from': trinity})
    usdn.approve(pool, 2**256-1, {'from': trinity})
    usdn._mint_for_testing(1 * DECIMALS, {'from': trinity})
    usdt.approve(pool, 2**256-1, {'from': trinity})
    usdt._mint_for_testing(1 * DECIMALS, {'from': morpheus})
    usdn.approve(pool, 2**256-1, {'from': morpheus})
    usdn._mint_for_testing(1 * DECIMALS, {'from': morpheus})
    usdt.approve(pool, 2**256-1, {'from': morpheus})

    # add liquidity for trinity and morpheus
    pool.add_liquidity([1 * DECIMALS, 1 * DECIMALS], 0, {'from': trinity})
    lp.approve(gauge, 2**256-1, {'from': trinity})
    pool.add_liquidity([1 * DECIMALS, 1 * DECIMALS], 0, {'from': morpheus})
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

    # no money on claimContract
    assert claimContract.claim_tokens(usdn) == 0
    assert claimContract.claim_tokens(usdt) == 0
    assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdn, {'from': morpheus}) == 0
    assert claimContract.claim_tokens(usdt, {'from': morpheus}) == 0

    # fill claimContract with money
    usdn._mint_for_testing(10 * DECIMALS, {'from': claimContract})
    usdt._mint_for_testing(10 * DECIMALS, {'from': claimContract})
    assert abs(usdn.balanceOf(claimContract) - 10 * DECIMALS) <= 10
    assert abs(usdt.balanceOf(claimContract) - 10 * DECIMALS) <= 10

    # check share reward for second holders (neo, trinity, morpheus)
    # print(claimContract.claimed_for(usdn, neo, {'from': neo}))
    assert (3.9 * DECIMALS <= claimContract.claim_tokens(usdn) <= 4.0 * DECIMALS)
    assert (3.9 * DECIMALS <= claimContract.claim_tokens(usdt) <= 4.0 * DECIMALS)
    assert (2.4 * DECIMALS <= claimContract.claim_tokens(usdn,
                                                         {'from': trinity}) <= 2.5 * DECIMALS)
    assert (2.4 * DECIMALS <= claimContract.claim_tokens(usdt,
                                                         {'from': trinity}) <= 2.5 * DECIMALS)
    assert (2.4 * DECIMALS <= claimContract.claim_tokens(usdn,
                                                         {'from': morpheus}) <= 2.5 * DECIMALS)
    assert (2.4 * DECIMALS <= claimContract.claim_tokens(usdt,
                                                         {'from': morpheus}) <= 2.5 * DECIMALS)
    assert claimContract.claim_tokens(usdn) + claimContract.claim_tokens(
        usdn, {'from': trinity}) + claimContract.claim_tokens(usdn, {'from': morpheus}) <= usdn.balanceOf(claimContract)
    assert claimContract.claim_tokens(usdt) + claimContract.claim_tokens(
        usdt, {'from': trinity}) + claimContract.claim_tokens(usdt, {'from': morpheus}) <= usdt.balanceOf(claimContract)

    # claim reward for neo
    claimContract.claim(usdn)  # 2.1
    claimContract.claim(usdt)  # 2.1
    assert (5.9 * DECIMALS <= usdn.balanceOf(neo) <= 6.0 * DECIMALS)  # 1.9 + 2
    assert (5.9 * DECIMALS <= usdt.balanceOf(neo) <= 6.0 * DECIMALS)  # 1.9 + 2
    assert (6 * DECIMALS <= usdn.balanceOf(claimContract) <= 6.1 * DECIMALS)
    assert (6 * DECIMALS <= usdt.balanceOf(claimContract) <= 6.1 * DECIMALS)

    # todo: impl
    # neo can't claim anymore
    assert claimContract.claim_tokens(usdn) == 0
    assert claimContract.claim_tokens(usdt) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn)
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt)

    # claim reward for trinity
    assert (2.4 * DECIMALS <= claimContract.claim_tokens(usdn,
                                                         {'from': trinity}) <= 2.5 * DECIMALS)
    assert (2.4 * DECIMALS <= claimContract.claim_tokens(usdt,
                                                         {'from': trinity}) <= 2.5 * DECIMALS)
    claimContract.claim(usdn, {'from': trinity})
    claimContract.claim(usdt, {'from': trinity})
    assert (2.4 * DECIMALS <= usdn.balanceOf(trinity,
                                             {'from': trinity}) <= 2.5 * DECIMALS)
    assert (2.4 * DECIMALS <= usdt.balanceOf(trinity,
                                             {'from': trinity}) <= 2.5 * DECIMALS)
    assert (3.5 * DECIMALS <= usdn.balanceOf(claimContract) <= 3.6 * DECIMALS)
    assert (3.5 * DECIMALS <= usdt.balanceOf(claimContract) <= 3.6 * DECIMALS)

    # trinity can't claim anymore
    assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn, {'from': trinity})
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt, {'from': trinity})

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

    # neo can't claim anymore
    assert claimContract.claim_tokens(usdn) == 0
    assert claimContract.claim_tokens(usdt) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn)
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt)

    # trinity can't claim anymore
    assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn, {'from': trinity})
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt, {'from': trinity})

    # fill claimContract with money
    usdn._mint_for_testing(10 * DECIMALS, {'from': claimContract})
    usdt._mint_for_testing(10 * DECIMALS, {'from': claimContract})
    assert (13.5 * DECIMALS <= usdn.balanceOf(claimContract) <= 13.6 * DECIMALS)
    assert (13.5 * DECIMALS <= usdt.balanceOf(claimContract) <= 13.6 * DECIMALS)

    # claim reward for morpheus
    claimContract.claim(usdn, {'from': morpheus})
    claimContract.claim(usdt, {'from': morpheus})
    assert (1.3 * DECIMALS <= usdn.balanceOf(morpheus,
                                             {'from': morpheus}) <= 1.4 * DECIMALS)
    assert (1.3 * DECIMALS <= usdt.balanceOf(morpheus,
                                             {'from': morpheus}) <= 1.4 * DECIMALS)
    assert (3.8 * DECIMALS <= usdn.balanceOf(claimContract) <= 3.9 * DECIMALS)
    assert (3.8 * DECIMALS <= usdt.balanceOf(claimContract) <= 3.9 * DECIMALS)

    #assert abs(usdn.balanceOf(claimContract)) <= 10
    #assert abs(usdt.balanceOf(claimContract)) <= 10
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
