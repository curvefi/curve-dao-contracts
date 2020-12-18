import brownie

DECIMALS = 10 ** 18


def test_claim(ERC20, ERC20LP, CurvePool, PoolProxy, VotingEscrow, GaugeController, Minter, LiquidityGauge, ClaimableReward2, accounts, token, chain):
    # init accounts
    deployer, neo, trinity, morpheus, garry, ron = accounts[:6]

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

    claimContract = ClaimableReward2.deploy(gauge, {'from': deployer})

    # first holder
    pool.add_liquidity([1 * DECIMALS, 1 * DECIMALS], 0, {'from': neo})
    assert usdn.balanceOf(pool) == 1 * DECIMALS
    assert usdn.balanceOf(proxy) == 0
    assert usdn.balanceOf(neo) == 0
    lp.approve(gauge, 2**256-1, {'from': neo})
    lp_balance_neo = lp.balanceOf(neo)
    gauge.deposit(lp_balance_neo, {'from': neo})

    for _ in range(7):
        chain.sleep(86400)

    assert usdn.balanceOf(pool) == 1 * DECIMALS
    assert usdn.balanceOf(proxy) == 0
    gauge.user_checkpoint(neo, {'from': neo})
    assert usdt.balanceOf(pool) == 1 * DECIMALS
    assert usdt.balanceOf(proxy) == 0

    # fill claimContract with money
    usdn._mint_for_testing(2 * DECIMALS, {'from': deployer})
    usdt._mint_for_testing(2 * DECIMALS, {'from': deployer})
    assert usdn.balanceOf(deployer) == 2 * DECIMALS
    assert usdt.balanceOf(deployer) == 2 * DECIMALS
    usdn.approve(claimContract, 2**256-1, {'from': deployer})
    usdt.approve(claimContract, 2**256-1, {'from': deployer})
    claimContract.deposit(usdn, 2 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdt, 2 * DECIMALS, {'from': deployer})

    # check share reward for first holder
    assert abs(claimContract.claimable_tokens(
        usdn, {'from': neo}) - 2 * DECIMALS) <= 10
    assert abs(claimContract.claimable_tokens(
        usdt, {'from': neo}) - 2 * DECIMALS) <= 10

    # claim 1st reward
    claimContract.claim(usdn, {'from': neo})
    claimContract.claim(usdt, {'from': neo})
    assert abs(usdn.balanceOf(neo) - 2 * DECIMALS) <= 10
    assert abs(usdt.balanceOf(neo) - 2 * DECIMALS) <= 10
    assert claimContract.claimable_tokens(usdn, {'from': neo}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': neo}) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn, {'from': neo})
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt, {'from': neo})

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

    for _ in range(7):
        chain.sleep(86400)

    gauge.user_checkpoint(neo, {'from': neo})
    gauge.user_checkpoint(trinity, {'from': trinity})
    gauge.user_checkpoint(morpheus, {'from': morpheus})

    # no money on claimContract
    assert claimContract.claimable_tokens(usdn, {'from': neo}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': neo}) == 0
    assert claimContract.claimable_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': trinity}) == 0
    assert claimContract.claimable_tokens(usdn, {'from': morpheus}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': morpheus}) == 0

    # fill claimContract with money
    usdn._mint_for_testing(10 * DECIMALS, {'from': deployer})
    usdt._mint_for_testing(10 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdn, 10 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdt, 10 * DECIMALS, {'from': deployer})

    # check 2nd share reward for second holders (neo, trinity, morpheus)
    assert (3.3 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': neo}) <= 3.34 * DECIMALS)
    assert (3.3 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': neo}) <= 3.34 * DECIMALS)
    assert (2.32 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': trinity}) <= 2.36 * DECIMALS)
    assert (2.32 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': trinity}) <= 2.36 * DECIMALS)
    assert (2.32 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': morpheus}) <= 2.36 * DECIMALS)
    assert (2.32 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': morpheus}) <= 2.36 * DECIMALS)
    assert claimContract.claimable_tokens(usdn, {'from': neo}) + claimContract.claimable_tokens(
        usdn, {'from': trinity}) + claimContract.claimable_tokens(usdn, {'from': morpheus}) <= usdn.balanceOf(claimContract)
    assert claimContract.claimable_tokens(usdt, {'from': neo}) + claimContract.claimable_tokens(
        usdt, {'from': trinity}) + claimContract.claimable_tokens(usdt, {'from': morpheus}) <= usdt.balanceOf(claimContract)

    # claim reward for neo
    claimContract.claim(usdn, {'from': neo})  # 3.3
    claimContract.claim(usdt, {'from': neo})  # 3.3
    assert (5.3 * DECIMALS <= usdn.balanceOf(neo) <= 5.4 * DECIMALS)  # 3.3 + 2
    assert (5.3 * DECIMALS <= usdt.balanceOf(neo) <= 5.4 * DECIMALS)  # 3.3 + 2
    assert (6.6 * DECIMALS <= usdn.balanceOf(claimContract) <= 6.67 * DECIMALS)
    assert (6.6 * DECIMALS <= usdt.balanceOf(claimContract) <= 6.67 * DECIMALS)

    # neo can't claim anymore
    assert claimContract.claimable_tokens(usdn, {'from': neo}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': neo}) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn, {'from': neo})
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt, {'from': neo})

    # claim reward for trinity
    assert (2.32 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': trinity}) <= 2.36 * DECIMALS)
    assert (2.32 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': trinity}) <= 2.36 * DECIMALS)
    claimContract.claim(usdn, {'from': trinity})
    claimContract.claim(usdt, {'from': trinity})
    assert (2.32 * DECIMALS <= usdn.balanceOf(trinity,
                                             {'from': trinity}) <= 2.36 * DECIMALS)
    assert (2.32 * DECIMALS <= usdt.balanceOf(trinity,
                                             {'from': trinity}) <= 2.36 * DECIMALS)
    assert (4.3 * DECIMALS <= usdn.balanceOf(claimContract) <= 4.35 * DECIMALS)
    assert (4.3 * DECIMALS <= usdt.balanceOf(claimContract) <= 4.35 * DECIMALS)

    # trinity can't claim anymore
    assert claimContract.claimable_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': trinity}) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn, {'from': trinity})
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt, {'from': trinity})

    for _ in range(7):
        chain.sleep(86400)

    gauge.user_checkpoint(neo, {'from': neo})
    gauge.user_checkpoint(trinity, {'from': trinity})
    gauge.user_checkpoint(morpheus, {'from': morpheus})

    # neo can't claim anymore
    assert claimContract.claimable_tokens(usdn, {'from': neo}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': neo}) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn, {'from': neo})
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt, {'from': neo})

    # trinity can't claim anymore
    assert claimContract.claimable_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': trinity}) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn, {'from': trinity})
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt, {'from': trinity})

    # morpheus still can claim rest of the money
    assert (2.9 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': morpheus}) <= 2.97 * DECIMALS)
    assert (2.9 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': morpheus}) <= 2.97 * DECIMALS)

    # fill claimContract with money
    usdn._mint_for_testing(12 * DECIMALS, {'from': deployer})
    usdt._mint_for_testing(12 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdn, 12 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdt, 12 * DECIMALS, {'from': deployer})
    assert (16.31 * DECIMALS <= usdn.balanceOf(claimContract) <= 16.35 * DECIMALS)
    assert (16.31 * DECIMALS <= usdt.balanceOf(claimContract) <= 16.35 * DECIMALS)

    # check 3rd share reward for neo, trinity, morpheus
    assert (3.99 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': neo}) <= 4.01 * DECIMALS)
    assert (3.99 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': neo}) <= 4.01 * DECIMALS)
    assert (3.99 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 4.01 * DECIMALS)
    assert (3.99 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 4.01 * DECIMALS)
    assert (5.8 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': morpheus}) <= 5.93 * DECIMALS)
    assert (5.8 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': morpheus}) <= 5.93 * DECIMALS)
    assert claimContract.claimable_tokens(usdn, {'from': neo}) + claimContract.claimable_tokens(
        usdn, {'from': trinity}) + claimContract.claimable_tokens(usdn, {'from': morpheus}) <= usdn.balanceOf(claimContract)
    assert claimContract.claimable_tokens(usdt, 
    {'from': neo}) + claimContract.claimable_tokens(
        usdt, {'from': trinity}) + claimContract.claimable_tokens(usdt, {'from': morpheus}) <= usdt.balanceOf(claimContract)

    # claim reward for morpheus (old reward + new reward)
    assert (5.8 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': morpheus}) <= 5.93 * DECIMALS)
    assert (5.8 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': morpheus}) <= 5.93 * DECIMALS)
    claimContract.claim(usdn, {'from': morpheus})
    claimContract.claim(usdt, {'from': morpheus})
    assert (5.8 * DECIMALS <= usdn.balanceOf(morpheus,
                                             {'from': morpheus}) <= 5.93 * DECIMALS)
    assert (5.8 * DECIMALS <= usdt.balanceOf(morpheus,
                                             {'from': morpheus}) <= 5.93 * DECIMALS)
    assert (10.39 * DECIMALS <= usdn.balanceOf(claimContract) <= 10.45 * DECIMALS)
    assert (10.39 * DECIMALS <= usdt.balanceOf(claimContract) <= 10.45 * DECIMALS)

    # morpheus can't claim anymore
    assert claimContract.claimable_tokens(usdn, {'from': morpheus}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': morpheus}) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn, {'from': morpheus})
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt, {'from': morpheus})

    # claim reward for trinity
    assert (3.99 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 4.01 * DECIMALS)
    assert (3.99 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 4.01 * DECIMALS)
    claimContract.claim(usdn, {'from': trinity})
    claimContract.claim(usdt, {'from': trinity})
    assert (6.32 * DECIMALS <= usdn.balanceOf(trinity,
                                             {'from': trinity}) <= 6.36 * DECIMALS)
    assert (6.32 * DECIMALS <= usdt.balanceOf(trinity,
                                             {'from': trinity}) <= 6.36 * DECIMALS)
    assert (6.39 * DECIMALS <= usdn.balanceOf(claimContract) <= 6.45 * DECIMALS)
    assert (6.39 * DECIMALS <= usdt.balanceOf(claimContract) <= 6.45 * DECIMALS)

    # trinity can't claim anymore
    assert claimContract.claimable_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': trinity}) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn, {'from': trinity})
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt, {'from': trinity})

    for _ in range(7):
        chain.sleep(86400)

    gauge.user_checkpoint(neo, {'from': neo})
    gauge.user_checkpoint(trinity, {'from': trinity})
    gauge.user_checkpoint(morpheus, {'from': morpheus})

    # fill claimContract with money
    usdn._mint_for_testing(3 * DECIMALS, {'from': deployer})
    usdt._mint_for_testing(3 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdn, 3 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdt, 3 * DECIMALS, {'from': deployer})
    assert (9.39 * DECIMALS <= usdn.balanceOf(claimContract) <= 9.45 * DECIMALS)
    assert (9.39 * DECIMALS <= usdt.balanceOf(claimContract) <= 9.45 * DECIMALS)

    # withdraw money from gauge for neo
    gauge.withdraw(lp_balance_neo, {'from': neo})
    gauge.user_checkpoint(neo, {'from': neo})

    # check 4th share reward for neo, trinity, morpheus
    assert (4.95 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': neo}) <= 5.01 * DECIMALS)
    assert (4.95 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': neo}) <= 5.01 * DECIMALS)
    assert (0.95 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 1.01 * DECIMALS)
    assert (0.95 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 1.01 * DECIMALS)
    assert (0.95 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 1.01 * DECIMALS)
    assert (0.95 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': morpheus}) <= 1.01 * DECIMALS)
    assert claimContract.claimable_tokens(usdn, {'from': neo}) + claimContract.claimable_tokens(
        usdn, {'from': trinity}) + claimContract.claimable_tokens(usdn, {'from': morpheus}) <= usdn.balanceOf(claimContract)
    assert claimContract.claimable_tokens(usdt, {'from': neo}) + claimContract.claimable_tokens(
        usdt, {'from': trinity}) + claimContract.claimable_tokens(usdt, {'from': morpheus}) <= usdt.balanceOf(claimContract)

    claimContract.claim(usdn, {'from': neo})
    claimContract.claim(usdt, {'from': neo})
    assert (10.3 * DECIMALS <= usdn.balanceOf(neo) <= 10.4 * DECIMALS)
    assert (10.3 * DECIMALS <= usdt.balanceOf(neo) <= 10.4 * DECIMALS)
    assert (4.39 * DECIMALS <= usdn.balanceOf(claimContract) <= 4.45 * DECIMALS)
    assert (4.39 * DECIMALS <= usdt.balanceOf(claimContract) <= 4.45 * DECIMALS)

    # neo can't claim anymore
    assert claimContract.claimable_tokens(usdn, {'from': neo}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': neo}) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn, {'from': neo})
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt, {'from': neo})

    assert (0.95 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 1.01 * DECIMALS)
    assert (0.95 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 1.01 * DECIMALS)
    assert (0.95 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 1.01 * DECIMALS)
    assert (0.95 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': morpheus}) <= 1.01 * DECIMALS)

    # both trinity and morpheus are not claiming during some time
    for _ in range(7):
        chain.sleep(86400)

    gauge.user_checkpoint(neo, {'from': neo})
    gauge.user_checkpoint(trinity, {'from': trinity})
    gauge.user_checkpoint(morpheus, {'from': morpheus})

    usdn._mint_for_testing(2 * DECIMALS, {'from': deployer})
    usdt._mint_for_testing(2 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdn, 2 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdt, 2 * DECIMALS, {'from': deployer})
    assert (6.39 * DECIMALS <= usdn.balanceOf(claimContract) <= 6.45 * DECIMALS)
    assert (6.39 * DECIMALS <= usdt.balanceOf(claimContract) <= 6.45 * DECIMALS)

    assert (2.45 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 2.51 * DECIMALS)
    assert (2.45 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 2.51 * DECIMALS)
    assert (2.45 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 2.51 * DECIMALS)
    assert (2.45 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': morpheus}) <= 2.51 * DECIMALS)

    for _ in range(7):
        chain.sleep(86400)

    gauge.user_checkpoint(neo, {'from': neo})
    gauge.user_checkpoint(trinity, {'from': trinity})
    gauge.user_checkpoint(morpheus, {'from': morpheus})

    usdn._mint_for_testing(2 * DECIMALS, {'from': deployer})
    usdt._mint_for_testing(2 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdn, 2 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdt, 2 * DECIMALS, {'from': deployer})
    assert (8.39 * DECIMALS <= usdn.balanceOf(claimContract) <= 8.45 * DECIMALS)
    assert (8.39 * DECIMALS <= usdt.balanceOf(claimContract) <= 8.45 * DECIMALS)

    assert (3.45 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 3.51 * DECIMALS)
    assert (3.45 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 3.51 * DECIMALS)
    assert (3.45 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 3.51 * DECIMALS)
    assert (3.45 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': morpheus}) <= 3.51 * DECIMALS)

    claimContract.claim(usdn, {'from': trinity})
    claimContract.claim(usdt, {'from': trinity})
    assert (9.8 * DECIMALS <= usdn.balanceOf(trinity) <= 9.9 * DECIMALS)
    assert (9.8 * DECIMALS <= usdt.balanceOf(trinity) <= 9.9 * DECIMALS)
    assert (4.89 * DECIMALS <= usdn.balanceOf(claimContract) <= 5.95 * DECIMALS)
    assert (4.89 * DECIMALS <= usdt.balanceOf(claimContract) <= 5.95 * DECIMALS)

    # morpheus is unlucky, his share is more than balanceOf(claimContract), so he picks share of balanceOf(claimContract) instead
    assert (3.45 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 3.51 * DECIMALS)
    assert (3.45 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': morpheus}) <= 3.51 * DECIMALS)

    # 2 guys are in with huge (garry) and little (ron) amounts
    # share money for garry and ron
    usdt._mint_for_testing(100 * DECIMALS, {'from': garry})
    usdn.approve(pool, 2**256-1, {'from': garry})
    usdn._mint_for_testing(100 * DECIMALS, {'from': garry})
    usdt.approve(pool, 2**256-1, {'from': garry})
    usdt._mint_for_testing(0.05 * DECIMALS, {'from': ron})
    usdn.approve(pool, 2**256-1, {'from': ron})
    usdn._mint_for_testing(0.05 * DECIMALS, {'from': ron})
    usdt.approve(pool, 2**256-1, {'from': ron})

    # add liquidity for garry and ron
    pool.add_liquidity([100 * DECIMALS, 100 * DECIMALS], 0, {'from': garry})
    lp.approve(gauge, 2**256-1, {'from': garry})
    pool.add_liquidity([0.05 * DECIMALS, 0.05 * DECIMALS], 0, {'from': ron})
    lp.approve(gauge, 2**256-1, {'from': ron})
    lp_balance_garry = lp.balanceOf(garry)
    gauge.deposit(lp.balanceOf(garry), {'from': garry})
    gauge.deposit(lp.balanceOf(ron), {'from': ron})

    for _ in range(7):
        chain.sleep(86400)

    gauge.user_checkpoint(neo, {'from': neo})
    gauge.user_checkpoint(trinity, {'from': trinity})
    gauge.user_checkpoint(morpheus, {'from': morpheus})
    gauge.user_checkpoint(garry, {'from': garry})
    gauge.user_checkpoint(ron, {'from': ron})

    # fill claimContract with money
    usdn._mint_for_testing(100 * DECIMALS, {'from': deployer})
    usdt._mint_for_testing(100 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdn, 100 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdt, 100 * DECIMALS, {'from': deployer})
    assert (104.89 * DECIMALS <= usdn.balanceOf(claimContract) <= 104.95 * DECIMALS)
    assert (104.89 * DECIMALS <= usdt.balanceOf(claimContract) <= 104.95 * DECIMALS)

    # split according to their shares
    assert (1.04 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 1.06 * DECIMALS)
    assert (1.04 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': morpheus}) <= 1.06 * DECIMALS)
    assert (0.97 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 0.98 * DECIMALS)
    assert (0.97 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 0.98 * DECIMALS)
    assert (0.55 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                               {'from': garry}) <= 0.57 * DECIMALS)
    assert (0.55 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                               {'from': garry}) <= 0.57 * DECIMALS)
    assert (0.0001 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                               {'from': ron}) <= 0.0005 * DECIMALS)
    assert (0.0001 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                               {'from': ron}) <= 0.0005 * DECIMALS)

    # withdraw money from gauge for garry, without any claims
    gauge.withdraw(lp_balance_garry, {'from': garry})
    gauge.user_checkpoint(garry, {'from': garry})

    # here ron is trying to claim
    assert (0.0001 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                               {'from': ron}) <= 0.0005 * DECIMALS)
    assert (0.0001 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                               {'from': ron}) <= 0.0005 * DECIMALS)

    for _ in range(7):
        chain.sleep(86400)

    gauge.user_checkpoint(neo, {'from': neo})
    gauge.user_checkpoint(trinity, {'from': trinity})
    gauge.user_checkpoint(morpheus, {'from': morpheus})
    gauge.user_checkpoint(garry, {'from': garry})
    gauge.user_checkpoint(ron, {'from': ron})

    # fill claimContract with money
    usdn._mint_for_testing(100 * DECIMALS, {'from': deployer})
    usdt._mint_for_testing(100 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdn, 100 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdt, 100 * DECIMALS, {'from': deployer})
    assert (204.89 * DECIMALS <= usdn.balanceOf(claimContract) <= 204.95 * DECIMALS)
    assert (204.89 * DECIMALS <= usdt.balanceOf(claimContract) <= 204.95 * DECIMALS)

    # here ron is trying to claim again
    assert (1.01 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': ron}) <= 1.04 * DECIMALS)
    assert (1.01 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': ron}) <= 1.04 * DECIMALS)

    # here morpheus is trying to claim again
    assert (100.97 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                                {'from': morpheus}) <= 100.98 * DECIMALS)
    assert (100.97 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                                {'from': morpheus}) <= 100.98 * DECIMALS)
    claimContract.claim(usdn, {'from': morpheus})
    claimContract.claim(usdt, {'from': morpheus})
    assert (106 * DECIMALS <= usdn.balanceOf(morpheus) <= 108 * DECIMALS)
    assert (106 * DECIMALS <= usdt.balanceOf(morpheus) <= 108 * DECIMALS)
    assert (103 * DECIMALS <= usdn.balanceOf(claimContract) <= 105 * DECIMALS)
    assert (103 * DECIMALS <= usdt.balanceOf(claimContract) <= 105 * DECIMALS)

    # garry is back, claiming his money
    assert (40 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                               {'from': garry}) <= 40.5 * DECIMALS)
    assert (40 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                               {'from': garry}) <= 40.5 * DECIMALS)
    claimContract.claim(usdn, {'from': garry})
    claimContract.claim(usdt, {'from': garry})
    assert (40 * DECIMALS <= usdn.balanceOf(garry) <= 40.5 * DECIMALS)
    assert (40 * DECIMALS <= usdt.balanceOf(garry) <= 40.5 * DECIMALS)

    # here ron is trying to claim again
    assert (1.01 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                               {'from': ron}) <= 1.05 * DECIMALS)
    assert (1.01 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                               {'from': ron}) <= 1.05 * DECIMALS)
    claimContract.claim(usdn, {'from': ron})
    claimContract.claim(usdt, {'from': ron})

    assert (30 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': trinity}) <= 31 * DECIMALS)
    assert (30 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': trinity}) <= 31 * DECIMALS)
    claimContract.claim(usdn, {'from': trinity})
    claimContract.claim(usdt, {'from': trinity})

    for _ in range(7):
        chain.sleep(86400)

    gauge.user_checkpoint(neo, {'from': neo})
    gauge.user_checkpoint(trinity, {'from': trinity})
    gauge.user_checkpoint(morpheus, {'from': morpheus})
    gauge.user_checkpoint(garry, {'from': garry})
    gauge.user_checkpoint(ron, {'from': ron})

    # fill claimContract with money
    usdn._mint_for_testing(100 * DECIMALS, {'from': deployer})
    usdt._mint_for_testing(100 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdn, 100 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdt, 100 * DECIMALS, {'from': deployer})
    assert (132 * DECIMALS <= usdn.balanceOf(claimContract) <= 135 * DECIMALS)
    assert (132 * DECIMALS <= usdt.balanceOf(claimContract) <= 135 * DECIMALS)

    # split according to their shares
    assert claimContract.claimable_tokens(usdn, {'from': garry}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': garry}) == 0
    assert claimContract.claimable_tokens(usdn, {'from': neo}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': neo}) == 0
    assert (48.78 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                               {'from': trinity}) <= 48.79 * DECIMALS)
    assert (48.78 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                               {'from': trinity}) <= 48.79 * DECIMALS)
    assert (48.78 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                               {'from': morpheus}) <= 48.79 * DECIMALS)
    assert (48.78 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                               {'from': morpheus}) <= 48.79 * DECIMALS)
    assert (2.43 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': ron}) <= 2.44 * DECIMALS)
    assert (2.43 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': ron}) <= 2.44 * DECIMALS)
    assert claimContract.claimable_tokens(usdn, {'from': ron}) + claimContract.claimable_tokens(
        usdn, {'from': trinity}) + claimContract.claimable_tokens(usdn, {'from': morpheus}) <= usdn.balanceOf(claimContract)
    assert claimContract.claimable_tokens(usdt, {'from': ron}) + claimContract.claimable_tokens(
        usdt, {'from': trinity}) + claimContract.claimable_tokens(usdt, {'from': morpheus}) <= usdt.balanceOf(claimContract)

    # emergency withdrawal
    with brownie.reverts("owner only"):
        claimContract.emergency_withdrawal(usdn, {'from': neo})
    with brownie.reverts("owner only"):
        claimContract.emergency_withdrawal(usdt, {'from': trinity})

    claimContract.emergency_withdrawal(usdn, {'from': deployer})
    assert usdn.balanceOf(claimContract) == 0

    claimContract.emergency_withdrawal(usdt, {'from': deployer})
    assert usdt.balanceOf(claimContract) == 0

    with brownie.reverts("zero amount"):
        claimContract.emergency_withdrawal(usdn, {'from': deployer})
    with brownie.reverts("zero amount"):
        claimContract.emergency_withdrawal(usdt, {'from': deployer})
        
    assert claimContract.claimable_tokens(usdn, {'from': neo}) == 0
    assert claimContract.claimable_tokens(usdn, {'from': trinity}) == 0
    assert claimContract.claimable_tokens(usdn, {'from': morpheus}) == 0
    assert claimContract.claimable_tokens(usdn, {'from': garry}) == 0
    assert claimContract.claimable_tokens(usdn, {'from': ron}) == 0
    assert claimContract.claimable_tokens(usdn, {'from': deployer}) == 0