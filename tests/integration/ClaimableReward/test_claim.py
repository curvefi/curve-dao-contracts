import brownie

DECIMALS = 10 ** 18


def test_claim(ERC20, ERC20LP, CurvePool, PoolProxy, VotingEscrow, GaugeController, Minter, LiquidityGauge, ClaimableReward, accounts, token, chain):
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

    claimContract = ClaimableReward.deploy(gauge, {'from': deployer})

    # first holder
    pool.add_liquidity([1 * DECIMALS, 1 * DECIMALS], 0, {'from': neo})
    assert usdn.balanceOf(pool) == 1 * DECIMALS
    assert usdn.balanceOf(proxy) == 0
    assert usdn.balanceOf(neo) == 0
    lp.approve(gauge, 2**256-1, {'from': neo})
    lp_balance_neo = lp.balanceOf(neo)
    gauge.deposit(lp_balance_neo, {'from': neo})

    claimContract.start_claiming(usdn, {'from': neo})
    claimContract.start_claiming(usdt, {'from': neo})

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

    with brownie.reverts("claim is not allowed"):
        claimContract.claimable_tokens(usdn, {'from': trinity})
    with brownie.reverts("claim is not allowed"):
        claimContract.claimable_tokens(usdt, {'from': trinity})
    with brownie.reverts("claim is not allowed"):
        claimContract.claimable_tokens(usdn, {'from': morpheus})
    with brownie.reverts("claim is not allowed"):
        claimContract.claimable_tokens(usdt, {'from': morpheus})

    with brownie.reverts("no lp tokens in gauge"):
        claimContract.start_claiming(usdn, {'from': trinity})
    with brownie.reverts("no lp tokens in gauge"):
        claimContract.start_claiming(usdt, {'from': trinity})
    with brownie.reverts("no lp tokens in gauge"):
        claimContract.start_claiming(usdn, {'from': morpheus})
    with brownie.reverts("no lp tokens in gauge"):
        claimContract.start_claiming(usdt, {'from': morpheus})

    with brownie.reverts("claim is not allowed"):
        claimContract.claimable_tokens(usdn, {'from': trinity})
    with brownie.reverts("claim is not allowed"):
        claimContract.claimable_tokens(usdt, {'from': trinity})
    with brownie.reverts("claim is not allowed"):
        claimContract.claimable_tokens(usdn, {'from': morpheus})
    with brownie.reverts("claim is not allowed"):
        claimContract.claimable_tokens(usdt, {'from': morpheus})

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

    claimContract.start_claiming(usdn, {'from': trinity})
    claimContract.start_claiming(usdt, {'from': trinity})
    claimContract.start_claiming(usdn, {'from': morpheus})
    claimContract.start_claiming(usdt, {'from': morpheus})

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
    assert (3.3 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': trinity}) <= 3.34 * DECIMALS)
    assert (3.3 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': trinity}) <= 3.34 * DECIMALS)
    assert (3.3 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': morpheus}) <= 3.34 * DECIMALS)
    assert (3.3 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': morpheus}) <= 3.34 * DECIMALS)
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
    assert (3.3 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': trinity}) <= 3.34 * DECIMALS)
    assert (3.3 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': trinity}) <= 3.34 * DECIMALS)
    claimContract.claim(usdn, {'from': trinity})
    claimContract.claim(usdt, {'from': trinity})
    assert (3.3 * DECIMALS <= usdn.balanceOf(trinity,
                                             {'from': trinity}) <= 3.34 * DECIMALS)
    assert (3.3 * DECIMALS <= usdt.balanceOf(trinity,
                                             {'from': trinity}) <= 3.34 * DECIMALS)
    assert (3.3 * DECIMALS <= usdn.balanceOf(claimContract) <= 3.34 * DECIMALS)
    assert (3.3 * DECIMALS <= usdt.balanceOf(claimContract) <= 3.34 * DECIMALS)

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
    assert (3.3 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': morpheus}) <= 3.34 * DECIMALS)
    assert (3.3 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': morpheus}) <= 3.34 * DECIMALS)

    # fill claimContract with money
    usdn._mint_for_testing(12 * DECIMALS, {'from': deployer})
    usdt._mint_for_testing(12 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdn, 12 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdt, 12 * DECIMALS, {'from': deployer})
    assert (15.3 * DECIMALS <= usdn.balanceOf(claimContract) <= 15.34 * DECIMALS)
    assert (15.3 * DECIMALS <= usdt.balanceOf(claimContract) <= 15.34 * DECIMALS)

    # check 3rd share reward for neo, trinity, morpheus
    assert (3.99 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': neo}) <= 4.01 * DECIMALS)
    assert (3.99 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': neo}) <= 4.01 * DECIMALS)
    assert (3.99 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 4.01 * DECIMALS)
    assert (3.99 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 4.01 * DECIMALS)
    assert (7.3 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': morpheus}) <= 7.34 * DECIMALS)
    assert (7.3 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': morpheus}) <= 7.34 * DECIMALS)
    assert claimContract.claimable_tokens(usdn, {'from': neo}) + claimContract.claimable_tokens(
        usdn, {'from': trinity}) + claimContract.claimable_tokens(usdn, {'from': morpheus}) <= usdn.balanceOf(claimContract)
    assert claimContract.claimable_tokens(usdt, {'from': neo}) + claimContract.claimable_tokens(
        usdt, {'from': trinity}) + claimContract.claimable_tokens(usdt, {'from': morpheus}) <= usdt.balanceOf(claimContract)

    # claim reward for morpheus (old reward + new reward)
    assert (7.3 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': morpheus}) <= 7.34 * DECIMALS)
    assert (7.3 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': morpheus}) <= 7.34 * DECIMALS)
    claimContract.claim(usdn, {'from': morpheus})
    claimContract.claim(usdt, {'from': morpheus})
    assert (7.3 * DECIMALS <= usdn.balanceOf(morpheus,
                                             {'from': morpheus}) <= 7.34 * DECIMALS)
    assert (7.3 * DECIMALS <= usdt.balanceOf(morpheus,
                                             {'from': morpheus}) <= 7.34 * DECIMALS)
    assert (7.99 * DECIMALS <= usdn.balanceOf(claimContract) <= 8.01 * DECIMALS)
    assert (7.99 * DECIMALS <= usdt.balanceOf(claimContract) <= 8.01 * DECIMALS)

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
    assert (7.3 * DECIMALS <= usdn.balanceOf(trinity,
                                             {'from': trinity}) <= 7.34 * DECIMALS)
    assert (7.3 * DECIMALS <= usdt.balanceOf(trinity,
                                             {'from': trinity}) <= 7.34 * DECIMALS)
    assert (3.99 * DECIMALS <= usdn.balanceOf(claimContract) <= 4.01 * DECIMALS)
    assert (3.99 * DECIMALS <= usdt.balanceOf(claimContract) <= 4.01 * DECIMALS)

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
    assert (7.0 * DECIMALS <= usdn.balanceOf(claimContract) <= 7.1 * DECIMALS)
    assert (7.0 * DECIMALS <= usdt.balanceOf(claimContract) <= 7.1 * DECIMALS)

    # withdraw money from gauge for neo
    gauge.withdraw(lp_balance_neo, {'from': neo})
    gauge.user_checkpoint(neo, {'from': neo})

    # check 4th share reward for neo, trinity, morpheus
    assert (4.99 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': neo}) <= 5.01 * DECIMALS)
    assert (4.99 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': neo}) <= 5.01 * DECIMALS)
    assert (0.99 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 1.01 * DECIMALS)
    assert (0.99 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 1.01 * DECIMALS)
    assert (0.99 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 1.01 * DECIMALS)
    assert (0.99 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': morpheus}) <= 1.01 * DECIMALS)
    assert claimContract.claimable_tokens(usdn, {'from': neo}) + claimContract.claimable_tokens(
        usdn, {'from': trinity}) + claimContract.claimable_tokens(usdn, {'from': morpheus}) <= usdn.balanceOf(claimContract)
    assert claimContract.claimable_tokens(usdt, {'from': neo}) + claimContract.claimable_tokens(
        usdt, {'from': trinity}) + claimContract.claimable_tokens(usdt, {'from': morpheus}) <= usdt.balanceOf(claimContract)

    claimContract.claim(usdn, {'from': neo})
    claimContract.claim(usdt, {'from': neo})
    assert (10.3 * DECIMALS <= usdn.balanceOf(neo) <= 10.4 * DECIMALS)
    assert (10.3 * DECIMALS <= usdt.balanceOf(neo) <= 10.4 * DECIMALS)
    assert (1.99 * DECIMALS <= usdn.balanceOf(claimContract) <= 2.01 * DECIMALS)
    assert (1.99 * DECIMALS <= usdt.balanceOf(claimContract) <= 2.01 * DECIMALS)

    # neo can't claim anymore
    assert claimContract.claimable_tokens(usdn, {'from': neo}) == 0
    assert claimContract.claimable_tokens(usdt, {'from': neo}) == 0
    with brownie.reverts("already claimed"):
        claimContract.claim(usdn, {'from': neo})
    with brownie.reverts("already claimed"):
        claimContract.claim(usdt, {'from': neo})

    assert (0.99 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 1.01 * DECIMALS)
    assert (0.99 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 1.01 * DECIMALS)
    assert (0.99 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 1.01 * DECIMALS)
    assert (0.99 * DECIMALS <= claimContract.claimable_tokens(usdt,
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
    assert (3.99 * DECIMALS <= usdn.balanceOf(claimContract) <= 4.01 * DECIMALS)
    assert (3.99 * DECIMALS <= usdt.balanceOf(claimContract) <= 4.01 * DECIMALS)

    assert (2.49 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 2.51 * DECIMALS)
    assert (2.49 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 2.51 * DECIMALS)
    assert (2.49 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 2.51 * DECIMALS)
    assert (2.49 * DECIMALS <= claimContract.claimable_tokens(usdt,
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
    assert (5.99 * DECIMALS <= usdn.balanceOf(claimContract) <= 6.01 * DECIMALS)
    assert (5.99 * DECIMALS <= usdt.balanceOf(claimContract) <= 6.01 * DECIMALS)

    assert (3.49 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 3.51 * DECIMALS)
    assert (3.49 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 3.51 * DECIMALS)
    assert (3.49 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 3.51 * DECIMALS)
    assert (3.49 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': morpheus}) <= 3.51 * DECIMALS)

    claimContract.claim(usdn, {'from': trinity})
    claimContract.claim(usdt, {'from': trinity})
    assert (10.8 * DECIMALS <= usdn.balanceOf(trinity) <= 10.9 * DECIMALS)
    assert (10.8 * DECIMALS <= usdt.balanceOf(trinity) <= 10.9 * DECIMALS)
    assert (2.49 * DECIMALS <= usdn.balanceOf(claimContract) <= 2.51 * DECIMALS)
    assert (2.49 * DECIMALS <= usdt.balanceOf(claimContract) <= 2.51 * DECIMALS)

    # morpheus is unlucky, his share is more than balanceOf(claimContract), so he picks share of balanceOf(claimContract) instead
    assert (1.25 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 1.251 * DECIMALS)
    assert (1.25 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': morpheus}) <= 1.251 * DECIMALS)

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

    claimContract.start_claiming(usdn, {'from': garry})
    claimContract.start_claiming(usdt, {'from': garry})
    claimContract.start_claiming(usdn, {'from': ron})
    claimContract.start_claiming(usdt, {'from': ron})

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
    assert (102.5 * DECIMALS <= usdn.balanceOf(claimContract) <= 102.51 * DECIMALS)
    assert (102.5 * DECIMALS <= usdt.balanceOf(claimContract) <= 102.51 * DECIMALS)

    # split according to their shares
    assert (1.04 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 1.06 * DECIMALS)
    assert (1.04 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': morpheus}) <= 1.06 * DECIMALS)
    assert (0.97 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 0.98 * DECIMALS)
    assert (0.97 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 0.98 * DECIMALS)
    assert (97.99 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                               {'from': garry}) <= 97.999 * DECIMALS)
    assert (97.99 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                               {'from': garry}) <= 97.999 * DECIMALS)
    assert (0.048 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                               {'from': ron}) <= 0.049 * DECIMALS)
    assert (0.048 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                               {'from': ron}) <= 0.049 * DECIMALS)

    # withdraw money from gauge for garry, without any claims
    gauge.withdraw(lp_balance_garry, {'from': garry})
    gauge.user_checkpoint(garry, {'from': garry})

    # here ron is trying to claim, still little money for him =|
    assert (0.048 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                               {'from': ron}) <= 0.049 * DECIMALS)
    assert (0.048 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                               {'from': ron}) <= 0.049 * DECIMALS)

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
    assert (202.5 * DECIMALS <= usdn.balanceOf(claimContract) <= 202.51 * DECIMALS)
    assert (202.5 * DECIMALS <= usdt.balanceOf(claimContract) <= 202.51 * DECIMALS)

    # here ron is trying to claim again, stonks
    assert (4.87 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': ron}) <= 4.88 * DECIMALS)
    assert (4.87 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': ron}) <= 4.88 * DECIMALS)

    # here morpheus is trying to claim again, super stonks
    assert (100.97 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                                {'from': morpheus}) <= 100.98 * DECIMALS)
    assert (100.97 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                                {'from': morpheus}) <= 100.98 * DECIMALS)
    claimContract.claim(usdn, {'from': morpheus})
    claimContract.claim(usdt, {'from': morpheus})
    assert (108.3 * DECIMALS <= usdn.balanceOf(morpheus) <= 108.4 * DECIMALS)
    assert (108.3 * DECIMALS <= usdt.balanceOf(morpheus) <= 108.4 * DECIMALS)
    assert (101.52 * DECIMALS <= usdn.balanceOf(claimContract)
            <= 101.53 * DECIMALS)
    assert (101.52 * DECIMALS <= usdt.balanceOf(claimContract)
            <= 101.53 * DECIMALS)

    # garry is back, claiming his money
    assert (97.52 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                               {'from': garry}) <= 97.53 * DECIMALS)
    assert (97.52 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                               {'from': garry}) <= 97.53 * DECIMALS)
    claimContract.claim(usdn, {'from': garry})
    claimContract.claim(usdt, {'from': garry})
    assert (97.52 * DECIMALS <= usdn.balanceOf(garry) <= 97.53 * DECIMALS)
    assert (97.52 * DECIMALS <= usdt.balanceOf(garry) <= 97.53 * DECIMALS)

    # here ron is trying to claim again, too late =( , wait for next deposit
    assert (0.097 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                               {'from': ron}) <= 0.098 * DECIMALS)
    assert (0.097 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                               {'from': ron}) <= 0.098 * DECIMALS)
    claimContract.claim(usdn, {'from': ron})
    claimContract.claim(usdt, {'from': ron})

    assert (1.9 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                             {'from': trinity}) <= 1.99 * DECIMALS)
    assert (1.9 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                             {'from': trinity}) <= 1.99 * DECIMALS)
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
    assert (101.9 * DECIMALS <= usdn.balanceOf(claimContract) <= 102 * DECIMALS)
    assert (101.9 * DECIMALS <= usdt.balanceOf(claimContract) <= 102 * DECIMALS)

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
