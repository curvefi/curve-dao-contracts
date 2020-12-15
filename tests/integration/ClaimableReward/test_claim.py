import brownie

DECIMALS = 10 ** 18


def test_claim(ERC20, ERC20LP, CurvePool, PoolProxy, VotingEscrow, GaugeController, Minter, LiquidityGauge, ClaimableReward, accounts, token, chain):
    # init accounts
    deployer, neo, trinity, morpheus = accounts[:4]

    # init contracts
    usdt = ERC20.deploy("Stable coin 1", "USDT", 18, {'from': deployer})
    usdn = ERC20.deploy("Stable coin 2", "USDN", 18, {'from': deployer})
    lp = ERC20LP.deploy("Curve LP token", "sCRV", 18, 0, {'from': deployer})

    pool = CurvePool.deploy([usdt, usdn], lp, 100, 4 *
                            10 ** 6, {'from': deployer})
    lp.set_minter(pool)

    proxy = PoolProxy.deploy(deployer, deployer, deployer, {'from': deployer})
    pool.commit_transfer_ownership(proxy)
    pool.apply_transfer_ownership()

    usdt._mint_for_testing(1 * DECIMALS, {'from': neo})
    usdn.approve(pool, 2**256-1, {'from': neo})
    usdn._mint_for_testing(1 * DECIMALS, {'from': neo})
    usdt.approve(pool, 2**256-1, {'from': neo})
    assert usdt.balanceOf(neo) == 1 * DECIMALS
    assert usdn.balanceOf(neo) == 1 * DECIMALS

    voting_escrow = VotingEscrow.deploy(
        token, 'Voting-escrowed CRV', 'veCRV', 'veCRV_0.99', {'from': deployer})
    controller = GaugeController.deploy(
        token, voting_escrow, {'from': deployer})
    minter = Minter.deploy(token, controller, {'from': deployer})
    gauge = LiquidityGauge.deploy(lp, minter, neo, {'from': deployer})

    controller.add_type("simple", 10, {'from': deployer})
    controller.add_gauge(gauge, 0, 10, {'from': deployer})

    claimContract = ClaimableReward.deploy(gauge, {'from': deployer})

    # first holder
    pool.add_liquidity([1 * DECIMALS, 1 * DECIMALS], 0, {'from': neo})
    assert usdn.balanceOf(pool) == 1 * DECIMALS
    assert usdn.balanceOf(proxy) == 0
    assert usdn.balanceOf(neo) == 0
    lp.approve(gauge, 2**256-1, {'from': neo})
    # chain.sleep(86400)
    lp_balance_neo = lp.balanceOf(neo)
    gauge.deposit(lp_balance_neo, {'from': neo})
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    chain.sleep(86400)
    assert usdn.balanceOf(pool) == 1 * DECIMALS
    assert usdn.balanceOf(proxy) == 0
    gauge.user_checkpoint(neo, {'from': neo})
    assert usdt.balanceOf(pool) == 1 * DECIMALS
    assert usdt.balanceOf(proxy) == 0

    # fill claimContract with money
    usdn._mint_for_testing(2 * DECIMALS, {'from': neo})
    usdt._mint_for_testing(2 * DECIMALS, {'from': neo})
    assert usdn.balanceOf(neo) == 2 * DECIMALS
    assert usdt.balanceOf(neo) == 2 * DECIMALS
    usdn.approve(claimContract, 2**256-1, {'from': neo})
    usdt.approve(claimContract, 2**256-1, {'from': neo})
    claimContract.deposit(usdn, 2 * DECIMALS, {'from': neo})
    claimContract.deposit(usdt, 2 * DECIMALS, {'from': neo})

    # check share reward for first holder
    assert abs(claimContract.claim_tokens(
        usdn, {'from': neo}) - 2 * DECIMALS) <= 10
    assert abs(claimContract.claim_tokens(
        usdt, {'from': neo}) - 2 * DECIMALS) <= 10
    assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    assert claimContract.claim_tokens(usdn, {'from': morpheus}) == 0
    assert claimContract.claim_tokens(usdt, {'from': morpheus}) == 0

    # # claim 1st reward
    # claimContract.claim(usdn)
    # claimContract.claim(usdt)
    # assert abs(usdn.balanceOf(neo) - 2 * DECIMALS) <= 10
    # assert abs(usdt.balanceOf(neo) - 2 * DECIMALS) <= 10
    # assert claimContract.claim_tokens(usdn) == 0
    # assert claimContract.claim_tokens(usdt) == 0
    # assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    # assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    # assert claimContract.claim_tokens(usdn, {'from': morpheus}) == 0
    # assert claimContract.claim_tokens(usdt, {'from': morpheus}) == 0

    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdn)
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdt)

    # # share money for trinity and morpheus
    # usdt._mint_for_testing(1 * DECIMALS, {'from': trinity})
    # usdn.approve(pool, 2**256-1, {'from': trinity})
    # usdn._mint_for_testing(1 * DECIMALS, {'from': trinity})
    # usdt.approve(pool, 2**256-1, {'from': trinity})
    # usdt._mint_for_testing(1 * DECIMALS, {'from': morpheus})
    # usdn.approve(pool, 2**256-1, {'from': morpheus})
    # usdn._mint_for_testing(1 * DECIMALS, {'from': morpheus})
    # usdt.approve(pool, 2**256-1, {'from': morpheus})

    # # add liquidity for trinity and morpheus
    # pool.add_liquidity([1 * DECIMALS, 1 * DECIMALS], 0, {'from': trinity})
    # lp.approve(gauge, 2**256-1, {'from': trinity})
    # pool.add_liquidity([1 * DECIMALS, 1 * DECIMALS], 0, {'from': morpheus})
    # lp.approve(gauge, 2**256-1, {'from': morpheus})
    # gauge.deposit(lp.balanceOf(trinity), {'from': trinity})
    # gauge.deposit(lp.balanceOf(morpheus), {'from': morpheus})

    # claimContract.claim(usdn, {'from': trinity})
    # claimContract.claim(usdt, {'from': trinity})
    # claimContract.claim(usdn, {'from': morpheus})
    # claimContract.claim(usdt, {'from': morpheus})

    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)

    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)

    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)

    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)

    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)

    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)

    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # # chain.sleep(86400)
    # gauge.user_checkpoint(neo)
    # gauge.user_checkpoint(trinity, {'from': trinity})
    # gauge.user_checkpoint(morpheus, {'from': morpheus})

    # # no money on claimContract
    # assert claimContract.claim_tokens(usdn) == 0
    # assert claimContract.claim_tokens(usdt) == 0
    # assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    # assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    # assert claimContract.claim_tokens(usdn, {'from': morpheus}) == 0
    # assert claimContract.claim_tokens(usdt, {'from': morpheus}) == 0

    # # fill claimContract with money
    # usdn._mint_for_testing(10 * DECIMALS, {'from': neo})
    # usdt._mint_for_testing(10 * DECIMALS, {'from': neo})
    # claimContract.deposit(usdn, 10 * DECIMALS, {'from': neo})
    # claimContract.deposit(usdt, 10 * DECIMALS, {'from': neo})

    # # check 2nd share reward for second holders (neo, trinity, morpheus)
    # assert (3.3 * DECIMALS <= claimContract.claim_tokens(usdn) <= 3.4 * DECIMALS)
    # assert (3.3 * DECIMALS <= claimContract.claim_tokens(usdt) <= 3.4 * DECIMALS)
    # assert (3.3 * DECIMALS <= claimContract.claim_tokens(usdn,
    #                                                      {'from': trinity}) <= 3.4 * DECIMALS)
    # assert (3.3 * DECIMALS <= claimContract.claim_tokens(usdt,
    #                                                      {'from': trinity}) <= 3.4 * DECIMALS)
    # assert (3.3 * DECIMALS <= claimContract.claim_tokens(usdn,
    #                                                      {'from': morpheus}) <= 3.4 * DECIMALS)
    # assert (3.3 * DECIMALS <= claimContract.claim_tokens(usdt,
    #                                                      {'from': morpheus}) <= 3.4 * DECIMALS)
    # assert claimContract.claim_tokens(usdn) + claimContract.claim_tokens(
    #     usdn, {'from': trinity}) + claimContract.claim_tokens(usdn, {'from': morpheus}) <= usdn.balanceOf(claimContract)
    # assert claimContract.claim_tokens(usdt) + claimContract.claim_tokens(
    #     usdt, {'from': trinity}) + claimContract.claim_tokens(usdt, {'from': morpheus}) <= usdt.balanceOf(claimContract)

    # # claim reward for neo
    # claimContract.claim(usdn)  # 1.9
    # claimContract.claim(usdt)  # 1.9
    # assert (5.3 * DECIMALS <= usdn.balanceOf(neo) <= 5.4 * DECIMALS)  # 1.9 + 2
    # assert (5.3 * DECIMALS <= usdt.balanceOf(neo) <= 5.4 * DECIMALS)  # 1.9 + 2
    # assert (6.6 * DECIMALS <= usdn.balanceOf(claimContract) <= 6.7 * DECIMALS)
    # assert (6.6 * DECIMALS <= usdt.balanceOf(claimContract) <= 6.7 * DECIMALS)

    # # neo can't claim anymore
    # assert claimContract.claim_tokens(usdn) == 0
    # assert claimContract.claim_tokens(usdt) == 0
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdn)
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdt)

    # # claim reward for trinity
    # assert (3.3 * DECIMALS <= claimContract.claim_tokens(usdn,
    #                                                      {'from': trinity}) <= 3.4 * DECIMALS)
    # assert (3.3 * DECIMALS <= claimContract.claim_tokens(usdt,
    #                                                      {'from': trinity}) <= 3.4 * DECIMALS)
    # claimContract.claim(usdn, {'from': trinity})
    # claimContract.claim(usdt, {'from': trinity})
    # assert (3.3 * DECIMALS <= usdn.balanceOf(trinity,
    #                                          {'from': trinity}) <= 3.4 * DECIMALS)
    # assert (3.3 * DECIMALS <= usdt.balanceOf(trinity,
    #                                          {'from': trinity}) <= 3.4 * DECIMALS)
    # assert (3.3 * DECIMALS <= usdn.balanceOf(claimContract) <= 3.4 * DECIMALS)
    # assert (3.3 * DECIMALS <= usdt.balanceOf(claimContract) <= 3.4 * DECIMALS)

    # # trinity can't claim anymore
    # assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    # assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdn, {'from': trinity})
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdt, {'from': trinity})

    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)
    # gauge.user_checkpoint(neo)
    # gauge.user_checkpoint(trinity, {'from': trinity})
    # gauge.user_checkpoint(morpheus, {'from': morpheus})

    # # neo can't claim anymore
    # assert claimContract.claim_tokens(usdn) == 0
    # assert claimContract.claim_tokens(usdt) == 0
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdn)
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdt)

    # # trinity can't claim anymore
    # assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    # assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdn, {'from': trinity})
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdt, {'from': trinity})

    # # morpheus still can claim rest of the money
    # assert (3.3 * DECIMALS <= claimContract.claim_tokens(usdn,
    #                                                      {'from': morpheus}) <= 3.4 * DECIMALS)
    # assert (3.3 * DECIMALS <= claimContract.claim_tokens(usdt,
    #                                                      {'from': morpheus}) <= 3.4 * DECIMALS)

    # # fill claimContract with money
    # usdn._mint_for_testing(12 * DECIMALS, {'from': neo})
    # usdt._mint_for_testing(12 * DECIMALS, {'from': neo})
    # claimContract.deposit(usdn, 12 * DECIMALS, {'from': neo})
    # claimContract.deposit(usdt, 12 * DECIMALS, {'from': neo})
    # assert (15.3 * DECIMALS <= usdn.balanceOf(claimContract) <= 15.4 * DECIMALS)
    # assert (15.3 * DECIMALS <= usdt.balanceOf(claimContract) <= 15.4 * DECIMALS)

    # # check 3rd share reward for neo, trinity, morpheus
    # assert (3.99 * DECIMALS <= claimContract.claim_tokens(usdn) <= 4.01 * DECIMALS)
    # assert (3.99 * DECIMALS <= claimContract.claim_tokens(usdt) <= 4.01 * DECIMALS)
    # assert (3.99 * DECIMALS <= claimContract.claim_tokens(usdn,
    #                                                       {'from': trinity}) <= 4.01 * DECIMALS)
    # assert (3.99 * DECIMALS <= claimContract.claim_tokens(usdt,
    #                                                       {'from': trinity}) <= 4.01 * DECIMALS)
    # assert (7.3 * DECIMALS <= claimContract.claim_tokens(usdn,
    #                                                      {'from': morpheus}) <= 7.4 * DECIMALS)
    # assert (7.3 * DECIMALS <= claimContract.claim_tokens(usdt,
    #                                                      {'from': morpheus}) <= 7.4 * DECIMALS)
    # assert claimContract.claim_tokens(usdn) + claimContract.claim_tokens(
    #     usdn, {'from': trinity}) + claimContract.claim_tokens(usdn, {'from': morpheus}) <= usdn.balanceOf(claimContract)
    # assert claimContract.claim_tokens(usdt) + claimContract.claim_tokens(
    #     usdt, {'from': trinity}) + claimContract.claim_tokens(usdt, {'from': morpheus}) <= usdt.balanceOf(claimContract)

    # # claim reward for morpheus (old reward + new reward)
    # assert (7.3 * DECIMALS <= claimContract.claim_tokens(usdn,
    #                                                      {'from': morpheus}) <= 7.4 * DECIMALS)
    # assert (7.3 * DECIMALS <= claimContract.claim_tokens(usdt,
    #                                                      {'from': morpheus}) <= 7.4 * DECIMALS)
    # claimContract.claim(usdn, {'from': morpheus})
    # claimContract.claim(usdt, {'from': morpheus})
    # assert (7.3 * DECIMALS <= usdn.balanceOf(morpheus,
    #                                          {'from': morpheus}) <= 7.4 * DECIMALS)
    # assert (7.3 * DECIMALS <= usdt.balanceOf(morpheus,
    #                                          {'from': morpheus}) <= 7.4 * DECIMALS)
    # assert (8.0 * DECIMALS <= usdn.balanceOf(claimContract) <= 8.01 * DECIMALS)
    # assert (8.0 * DECIMALS <= usdt.balanceOf(claimContract) <= 8.01 * DECIMALS)

    # # morpheus can't claim anymore
    # assert claimContract.claim_tokens(usdn, {'from': morpheus}) == 0
    # assert claimContract.claim_tokens(usdt, {'from': morpheus}) == 0
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdn, {'from': morpheus})
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdt, {'from': morpheus})

    # # claim reward for trinity
    # assert (3.99 * DECIMALS <= claimContract.claim_tokens(usdn,
    #                                                       {'from': trinity}) <= 4.0 * DECIMALS)
    # assert (3.99 * DECIMALS <= claimContract.claim_tokens(usdt,
    #                                                       {'from': trinity}) <= 4.0 * DECIMALS)
    # claimContract.claim(usdn, {'from': trinity})
    # claimContract.claim(usdt, {'from': trinity})
    # assert (7.3 * DECIMALS <= usdn.balanceOf(trinity,
    #                                          {'from': trinity}) <= 7.4 * DECIMALS)
    # assert (7.3 * DECIMALS <= usdt.balanceOf(trinity,
    #                                          {'from': trinity}) <= 7.4 * DECIMALS)
    # assert (4.0 * DECIMALS <= usdn.balanceOf(claimContract) <= 4.1 * DECIMALS)
    # assert (4.0 * DECIMALS <= usdt.balanceOf(claimContract) <= 4.1 * DECIMALS)

    # # trinity can't claim anymore
    # assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    # assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdn, {'from': trinity})
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdt, {'from': trinity})

    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)
    # chain.sleep(86400)
    # gauge.user_checkpoint(neo)
    # gauge.user_checkpoint(trinity, {'from': trinity})
    # gauge.user_checkpoint(morpheus, {'from': morpheus})

    # # fill claimContract with money
    # usdn._mint_for_testing(3 * DECIMALS, {'from': neo})
    # usdt._mint_for_testing(3 * DECIMALS, {'from': neo})
    # claimContract.deposit(usdn, 3 * DECIMALS, {'from': neo})
    # claimContract.deposit(usdt, 3 * DECIMALS, {'from': neo})
    # assert (7.0 * DECIMALS <= usdn.balanceOf(claimContract) <= 7.1 * DECIMALS)
    # assert (7.0 * DECIMALS <= usdt.balanceOf(claimContract) <= 7.1 * DECIMALS)

    # # withdraw money from gauge for neo
    # gauge.withdraw(lp_balance_neo, {'from': neo})
    # gauge.user_checkpoint(neo)

    # # # neo can't claim anymore
    # assert claimContract.claim_tokens(usdn) == 0
    # assert claimContract.claim_tokens(usdt) == 0
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdn)
    # # with brownie.reverts("already claimed"):
    # #     claimContract.claim(usdt)

    # # check 4th share reward for neo, trinity, morpheus
    # assert claimContract.claim_tokens(usdn) == 0
    # assert claimContract.claim_tokens(usdt) == 0
    # assert (1.49 * DECIMALS <= claimContract.claim_tokens(usdn,
    #                                                       {'from': trinity}) <= 1.51 * DECIMALS)
    # assert (1.49 * DECIMALS <= claimContract.claim_tokens(usdt,
    #                                                       {'from': trinity}) <= 1.51 * DECIMALS)
    # assert (1.49 * DECIMALS <= claimContract.claim_tokens(usdn,
    #                                                       {'from': morpheus}) <= 1.51 * DECIMALS)
    # assert (1.49 * DECIMALS <= claimContract.claim_tokens(usdt,
    #                                                       {'from': morpheus}) <= 1.51 * DECIMALS)
    # assert claimContract.claim_tokens(usdn) + claimContract.claim_tokens(
    #     usdn, {'from': trinity}) + claimContract.claim_tokens(usdn, {'from': morpheus}) <= usdn.balanceOf(claimContract)
    # assert claimContract.claim_tokens(usdt) + claimContract.claim_tokens(
    #     usdt, {'from': trinity}) + claimContract.claim_tokens(usdt, {'from': morpheus}) <= usdt.balanceOf(claimContract)

    # #assert abs(usdn.balanceOf(claimContract)) <= 10
    # #assert abs(usdt.balanceOf(claimContract)) <= 10
    # # # claimContract.claim(usdn, {'from': trinity})
    # # # claimContract.claim(usdn, {'from': morpheus})
    # # # claimContract.claim(usdt, {'from': trinity})
    # # # claimContract.claim(usdt, {'from': morpheus})
    # # # assert claimContract.claim_tokens(usdn, {'from': neo}) == 0
    # # # assert claimContract.claim_tokens(usdt, {'from': neo}) == 0
    # # # assert claimContract.claim_tokens(usdn, {'from': trinity}) == 0
    # # # assert claimContract.claim_tokens(usdt, {'from': trinity}) == 0
    # # # assert claimContract.claim_tokens(usdn, {'from': morpheus}) == 0
    # # # assert claimContract.claim_tokens(usdt, {'from': morpheus}) == 0

    # # # assert usdn.balanceOf(neo) + usdn.balanceOf(trinity) + \
    # # #     usdn.balanceOf(morpheus) < 2 * 10 ** 18
    # # # assert usdt.balanceOf(neo) + usdt.balanceOf(trinity) + \
    # # #     usdt.balanceOf(morpheus) < 2 * 10 ** 18

    # # # usdn._mint_for_testing(2 * 10 ** 18, {'from': neo})
    # # # usdt._mint_for_testing(2 * 10 ** 18, {'from': neo})
    # # # usdn.transfer(claimContract, 2 * 10 ** 18, {'from': neo})
    # # # usdt.transfer(claimContract, 2 * 10 ** 18, {'from': neo})
    # # # chain.sleep(86400)
    # # # chain.sleep(86400)
    # # # chain.sleep(86400)
    # # # chain.sleep(86400)
    # # # chain.sleep(86400)
    # # # chain.sleep(86400)
    # # # chain.sleep(86400)
    # # # gauge.user_checkpoint(neo)
    # # # gauge.user_checkpoint(trinity, {'from': trinity})
    # # # gauge.user_checkpoint(morpheus, {'from': morpheus})

    # # # # assert claimContract.claim_tokens(usdn) == 0
    # # # # assert claimContract.claim_tokens(usdt) == 0

    # # # assert claimContract.claim_tokens(
    # # #     usdn, {'from': morpheus}) == 0

    # # # # assert abs(claimContract.claim_tokens(
    # # # # usdn, {'from': trinity}) - 0.1178 * 10**18) < 10 ** 15
    # # # # assert abs(claimContract.claim_tokens(
    # # # # usdt, {'from': trinity}) - 0.1178 * 10**18) < 10 ** 15
    # # # assert abs(claimContract.claim_tokens(
    # # #     usdn, {'from': morpheus}) - 0.1178 * 10**18) < 10 ** 15
    # # # assert abs(claimContract.claim_tokens(
    # # #     usdt, {'from': morpheus}) - 0.1178 * 10**18) < 10 ** 15
