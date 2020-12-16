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

    claimContract.start_claiming(usdn, {'from': neo})
    claimContract.start_claiming(usdt, {'from': neo})

    for _ in range(7):
        chain.sleep(86400)

    assert usdn.balanceOf(pool) == 1 * DECIMALS
    assert usdn.balanceOf(proxy) == 0
    gauge.user_checkpoint(neo, {'from': neo})
    assert usdt.balanceOf(pool) == 1 * DECIMALS
    assert usdt.balanceOf(proxy) == 0

    # print("gauge.integrate_fraction(neo)=", gauge.integrate_fraction(neo))
    # print("gauge.integrate_fraction(trinity)=", gauge.integrate_fraction(trinity))
    # print("gauge.integrate_fraction(morpheus)=", gauge.integrate_fraction(morpheus))
    # print("gauge.integrate_inv_supply_of(neo)=", gauge.integrate_inv_supply_of(neo))
    # print("gauge.integrate_inv_supply_of(trinity)=", gauge.integrate_inv_supply_of(trinity))
    # print("gauge.integrate_inv_supply_of(morpheus)=", gauge.integrate_inv_supply_of(morpheus))
    # print("gauge.integrate_inv_supply(gauge.period())=", gauge.integrate_inv_supply(gauge.period()))

    # fill claimContract with money
    usdn._mint_for_testing(2 * DECIMALS, {'from': deployer})
    usdt._mint_for_testing(2 * DECIMALS, {'from': deployer})
    assert usdn.balanceOf(deployer) == 2 * DECIMALS
    assert usdt.balanceOf(deployer) == 2 * DECIMALS
    usdn.approve(claimContract, 2**256-1, {'from': deployer})
    usdt.approve(claimContract, 2**256-1, {'from': deployer})
    claimContract.deposit(usdn, 2 * DECIMALS, {'from': deployer})
    claimContract.deposit(usdt, 2 * DECIMALS, {'from': deployer})

    print(gauge.working_supply())
    print(gauge.integrate_fraction(neo))
    print(gauge.integrate_inv_supply_of(neo))
    print(claimContract.integrated_deposit(usdn))

    # check share reward for first holder
    assert abs(claimContract.claimable_tokens(
        usdn, {'from': neo}) - 2 * DECIMALS) <= 10
    assert abs(claimContract.claimable_tokens(
        usdt, {'from': neo}) - 2 * DECIMALS) <= 10

    # # claim 1st reward
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

    claimContract.start_claiming(usdn, {'from': trinity})
    claimContract.start_claiming(usdt, {'from': trinity})
    claimContract.start_claiming(usdn, {'from': morpheus})
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

    # print("gauge.integrate_fraction(neo)=", gauge.integrate_fraction(neo))
    # print("gauge.integrate_fraction(trinity)=", gauge.integrate_fraction(trinity))
    # print("gauge.integrate_fraction(morpheus)=", gauge.integrate_fraction(morpheus))
    # print("gauge.integrate_inv_supply_of(neo)=", gauge.integrate_inv_supply_of(neo))
    # print("gauge.integrate_inv_supply_of(trinity)=", gauge.integrate_inv_supply_of(trinity))
    # print("gauge.integrate_inv_supply_of(morpheus)=", gauge.integrate_inv_supply_of(morpheus))
    # print("gauge.integrate_inv_supply(gauge.period())=", gauge.integrate_inv_supply(gauge.period()))
    # print("gauge.working_supply()=", gauge.working_supply())

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

    for _ in range(5):
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

    for _ in range(5):
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
    for _ in range(5):
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

    print("integr_deposit=", claimContract.integrated_deposit(usdn))
    print("commited_deposit_for=", claimContract.commited_deposit_for(usdn, neo))
    print("commited_deposit_for=", claimContract.commited_deposit_for(usdn, trinity))
    print("commited_deposit_for=", claimContract.commited_deposit_for(usdn, morpheus))

    assert (2.49 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': trinity}) <= 2.51 * DECIMALS)
    assert (2.49 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': trinity}) <= 2.51 * DECIMALS)
    assert (2.49 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 2.51 * DECIMALS)
    assert (2.49 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': morpheus}) <= 2.51 * DECIMALS)

    for _ in range(5):
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

    assert (3.49 * DECIMALS <= claimContract.claimable_tokens(usdn,
                                                              {'from': morpheus}) <= 3.51 * DECIMALS)
    assert (3.49 * DECIMALS <= claimContract.claimable_tokens(usdt,
                                                              {'from': morpheus}) <= 3.51 * DECIMALS)

    # 2 kosiposhas are in


    assert False
    # # assert abs(usdn.balanceOf(claimContract)) <= 10
    # # assert abs(usdt.balanceOf(claimContract)) <= 10
    # # # claimContract.claim(usdn, {'from': trinity})
    # # # claimContract.claim(usdn, {'from': morpheus})
    # # # claimContract.claim(usdt, {'from': trinity})
    # # # claimContract.claim(usdt, {'from': morpheus})
    # # # assert claimContract.claimable_tokens(usdn, {'from': neo}) == 0
    # # # assert claimContract.claimable_tokens(usdt, {'from': neo}) == 0
    # # # assert claimContract.claimable_tokens(usdn, {'from': trinity}) == 0
    # # # assert claimContract.claimable_tokens(usdt, {'from': trinity}) == 0
    # # # assert claimContract.claimable_tokens(usdn, {'from': morpheus}) == 0
    # # # assert claimContract.claimable_tokens(usdt, {'from': morpheus}) == 0

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

    # # # # assert claimContract.claimable_tokens(usdn) == 0
    # # # # assert claimContract.claimable_tokens(usdt) == 0

    # # # assert claimContract.claimable_tokens(
    # # #     usdn, {'from': morpheus}) == 0

    # # # # assert abs(claimContract.claimable_tokens(
    # # # # usdn, {'from': trinity}) - 0.1178 * 10**18) < 10 ** 15
    # # # # assert abs(claimContract.claimable_tokens(
    # # # # usdt, {'from': trinity}) - 0.1178 * 10**18) < 10 ** 15
    # # # assert abs(claimContract.claimable_tokens(
    # # #     usdn, {'from': morpheus}) - 0.1178 * 10**18) < 10 ** 15
    # # # assert abs(claimContract.claimable_tokens(
    # # #     usdt, {'from': morpheus}) - 0.1178 * 10**18) < 10 ** 15
