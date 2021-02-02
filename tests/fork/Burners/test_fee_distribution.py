from brownie import (
    ZERO_ADDRESS,
    ABurner,
    BTCBurner,
    CBurner,
    Contract,
    ETHBurner,
    EuroBurner,
    FeeDistributor,
    LPBurner,
    MetaBurner,
    PoolProxy,
    UnderlyingBurner,
    USDNBurner,
    YBurner,
    accounts,
    chain,
    history,
)

BURNERS = {
    LPBurner: ["0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3"],  # sbtcCRV
    BTCBurner: [
        "0xeb4c2781e4eba804ce9a9803c67d0893436bb27d",  # renBTC
        "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # wBTC
        "0x0316EB71485b0Ab14103307bf65a021042c6d380",  # hBTC
        "0x8dAEBADE922dF735c38C80C7eBD708Af50815fAa",  # tBTC
        "0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6",  # sBTC
    ],
    ETHBurner: [
        "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",  # stETH
        # "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",  # ETH
        "0x5e74C9036fb86BD7eCdcb084a0673EFc32eA31cb",  # sETH
    ],
    EuroBurner: [
        "0xdB25f211AB05b1c97D595516F45794528a807ad8",  # EURS
        "0xD71eCFF9342A5Ced620049e616c5035F1dB98620",  # sEUR
    ],
    ABurner: [
        "0x028171bCA77440897B824Ca71D1c56caC55b68A3",  # aDAI
        "0xBcca60bB61934080951369a648Fb03DF4F96263C",  # aUSDC
        "0x3Ed3B47Dd13EC9a98b44e6204A523E766B225811",  # aUSDT
    ],
    CBurner: [
        "0x39aa39c021dfbae8fac545936693ac917d5e7563",  # cDAI
        "0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",  # cUSDC
    ],
    YBurner: [
        "0xC2cB1040220768554cf699b0d863A3cd4324ce32",  # y/yDAI
        "0x26EA744E5B887E5205727f55dFBE8685e3b21951",  # y/yUSDC
        "0xE6354ed5bC4b393a5Aad09f21c46E101e692d447",  # y/yUSDT
        "0x16de59092dAE5CcF4A1E6439D611fd0653f0Bd01",  # busd/yDAI
        "0xd6aD7a6750A7593E092a9B218d66C0A814a3436e",  # busd/yUSDC
        "0x83f798e925BcD4017Eb265844FDDAbb448f1707D",  # busd/yUSDT
        "0x99d1Fa417f94dcD62BfE781a1213c092a47041Bc",  # pax/yDAI
        "0x9777d7E2b60bB01759D0E2f8be2095df444cb07E",  # pax/yUSDC
        "0x1bE5d71F2dA660BFdee8012dDc58D024448A0A59",  # pax/yUSDT
        "0x04bC0Ab673d88aE9dbC9DA2380cB6B79C4BCa9aE",  # yTUSD
        "0x73a052500105205d34Daf004eAb301916DA8190f",  # yBUSD
    ],
    MetaBurner: [
        "0x056fd409e1d7a124bd7017459dfea2f387b6d5cd",  # GUSD
        "0xdf574c24545e5ffecb9a659c229253d4111d87e1",  # HUSD
        "0x1c48f86ae57291f7686349f12601910bd8d470bb",  # USDK
        "0x0E2EC54fC0B509F445631Bf4b91AB8168230C752",  # LinkUSD
        "0xe2f2a5C287993345a840Db3B0845fbC70f5935a5",  # MUSD
        "0x196f4727526eA7FB1e17b2071B3d8eAA38486988",  # RSV
        "0x5bc25f649fc4e26069ddf4cf4010f9f706c23831",  # DUSD
    ],
    USDNBurner: ["0x674C6Ad92Fd080e4004b2312b45f796a192D27a0"],  # USDN
    UnderlyingBurner: [
        "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        "0x8e870d67f660d95d5be530380d0ec0bd388289e1",  # PAX
        "0x57ab1ec28d129707052df4df418d58a2d46d5f51",  # sUSD
    ],
}


def test_fee_distribution():

    alice = accounts[0]
    lp_tripool = Contract("0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490")

    # get list of active pools
    provider = Contract("0x0000000022D53366457F9d5E68Ec105046FC4383")
    registry = Contract(provider.get_registry())
    pool_list = [Contract(registry.pool_list(i)) for i in range(registry.pool_count())]

    # deploy new pool proxy
    proxy = PoolProxy.deploy(alice, alice, alice, {"from": alice})

    # transfer ownership of all pools to new pool proxy
    for pool in pool_list:
        owner = pool.owner()
        pool.commit_transfer_ownership(proxy, {"from": owner})

    chain.sleep(86400 * 3)

    for pool in pool_list:
        owner = pool.owner()
        pool.apply_transfer_ownership({"from": owner})

    # yes, we are traveling back in time here
    # this is necessary so that SNX oracle data is not considered outdated
    chain.mine(timestamp=history[0].timestamp)

    # deploy the fee distributor
    distributor = FeeDistributor.deploy(
        "0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2",  # VotingEscrow
        chain.time(),
        lp_tripool,
        alice,
        alice,
        {"from": alice},
    )

    # deploy the burners
    underlying_burner = UnderlyingBurner.deploy(distributor, alice, alice, alice, {"from": alice})
    MetaBurner.deploy(distributor, alice, alice, alice, {"from": alice})
    usdn_burner = USDNBurner.deploy(proxy, distributor, alice, alice, alice, {"from": alice})

    btc_burner = BTCBurner.deploy(underlying_burner, alice, alice, alice, {"from": alice})
    ETHBurner.deploy(underlying_burner, alice, alice, alice, {"from": alice})
    EuroBurner.deploy(underlying_burner, alice, alice, alice, {"from": alice})

    ABurner.deploy(underlying_burner, alice, alice, alice, {"from": alice})
    CBurner.deploy(underlying_burner, alice, alice, alice, {"from": alice})
    YBurner.deploy(underlying_burner, alice, alice, alice, {"from": alice})

    lp_burner = LPBurner.deploy(alice, alice, alice, {"from": alice})

    # set LP burner to unwrap sbtcCRV -> sBTC and transfer to BTC burner
    lp_burner.set_swap_data(
        "0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3",
        "0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6",
        btc_burner,
    )

    # set the burners within pool proxy
    to_set = [(k[-1], x) for k, v in BURNERS.items() for x in v]
    burners = [i[0] for i in to_set] + [ZERO_ADDRESS] * (40 - len(to_set))
    coins = [i[1] for i in to_set] + [ZERO_ADDRESS] * (40 - len(to_set))

    coin_list = [Contract(x) for v in BURNERS.values() for x in v]
    burner_list = [k[-1] for k in BURNERS.keys()]

    proxy.set_many_burners(coins[:20], burners[:20], {"from": alice})
    proxy.set_many_burners(coins[20:], burners[20:], {"from": alice})
    proxy.set_burner(lp_tripool, distributor, {"from": alice})

    # approve USDN burner to donate to USDN pool
    proxy.set_donate_approval(
        "0x0f9cb53Ebe405d49A0bbdBD291A65Ff571bC83e1", usdn_burner, True, {"from": alice}
    )

    # withdraw pool fees to pool proxy
    proxy.withdraw_many(pool_list[:20], {"from": alice})
    proxy.withdraw_many(
        pool_list[20:] + [ZERO_ADDRESS] * (20 - len(pool_list[20:])), {"from": alice}
    )

    # individually execute the burners for each coin
    for coin in coin_list + [lp_tripool]:
        if coin == "0x57ab1ec28d129707052df4df418d58a2d46d5f51":
            # for sUSD we settle manually to avoid a ganache bug
            chain.sleep(700)
            Contract("0x0bfDc04B38251394542586969E2356d0D731f7DE").settle(
                underlying_burner,
                "0x7355534400000000000000000000000000000000000000000000000000000000",
                {"from": alice},
            )
        proxy.burn(coin, {"from": alice})

    # call execute on underlying burner
    underlying_burner.execute({"from": alice})

    # verify zero-balances for all tokens in all contracts
    for coin in coin_list:
        for burner in burner_list:
            assert coin.balanceOf(burner) < 2
        assert coin.balanceOf(proxy) < 2
        assert coin.balanceOf(alice) < 2
        assert coin.balanceOf(distributor) < 2

    # verify zero-balance for 3CRV
    for burner in burner_list:
        assert lp_tripool.balanceOf(burner) == 0
    assert lp_tripool.balanceOf(proxy) == 0
    assert lp_tripool.balanceOf(alice) == 0

    # verify that fee distributor has received 3CRV
    amount = lp_tripool.balanceOf(distributor)
    assert amount > 0
    print(f"Success! Final 3CRV balance in distributor: {amount/1e18:.4f}")
