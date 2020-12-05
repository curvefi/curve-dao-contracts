from brownie import (
    BTCBurner,
    CBurner,
    Contract,
    FeeDistributor,
    LPBurner,
    MetaBurner,
    PoolProxy,
    UnderlyingBurner,
    USDNBurner,
    YBurner,
    ZERO_ADDRESS,
    accounts,
)

# modify me prior to deployment on mainnet!
DEPLOYER = accounts.at("0x7EeAC6CDdbd1D0B8aF061742D41877D7F707289a", force=True)

OWNER_ADMIN = "0x40907540d8a6C65c637785e8f8B742ae6b0b9968"
PARAM_ADMIN = "0x4EEb3bA4f221cA16ed4A0cC7254E2E32DF948c5f"
EMERGENCY_ADMIN = "0x00669DF67E4827FCc0E48A1838a8d5AB79281909"
RECOVERY = "0xae9c8320a6394120ecb7b2b2678d9b4ac848d106"


BURNERS = {
    BTCBurner: [
        "0xeb4c2781e4eba804ce9a9803c67d0893436bb27d",  # renBTC
        "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # wBTC
        "0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6",  # sBTC
        "0x0316EB71485b0Ab14103307bf65a021042c6d380",  # hBTC
        "0x8dAEBADE922dF735c38C80C7eBD708Af50815fAa",  # tBTC
    ],
    CBurner: [
        "0x39aa39c021dfbae8fac545936693ac917d5e7563",  # cDAI
        "0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",  # cUSDC
    ],
    LPBurner: [
        "0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3"  # sbtcCRV
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
    UnderlyingBurner: [
        "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        "0x8e870d67f660d95d5be530380d0ec0bd388289e1",  # PAX
        "0x57ab1ec28d129707052df4df418d58a2d46d5f51",  # sUSD
    ],
    USDNBurner: [
        "0x674C6Ad92Fd080e4004b2312b45f796a192D27a0",  # USDN
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
}


def main(deployer=DEPLOYER):
    initial_balance = deployer.balance()
    lp_tripool = Contract("0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490")

    # deploy new pool proxy
    proxy = PoolProxy.deploy(deployer, deployer, deployer, {"from": deployer})

    # sept 17, 2020 - 2 days before admin fee collection begins
    start_time = 1600300800

    # deploy the fee distributor
    distributor = FeeDistributor.deploy(
        "0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2",  # VotingEscrow
        start_time,
        lp_tripool,
        OWNER_ADMIN,
        EMERGENCY_ADMIN,
        {'from': deployer}
    )

    # deploy the burners
    underlying_burner = UnderlyingBurner.deploy(distributor, RECOVERY, OWNER_ADMIN, EMERGENCY_ADMIN, {'from': deployer})
    meta_burner = MetaBurner.deploy(distributor, RECOVERY, OWNER_ADMIN, EMERGENCY_ADMIN, {'from': deployer})
    usdn_burner = USDNBurner.deploy(proxy, distributor, RECOVERY, OWNER_ADMIN, EMERGENCY_ADMIN, {'from': deployer})

    btc_burner = BTCBurner.deploy(underlying_burner, RECOVERY, OWNER_ADMIN, EMERGENCY_ADMIN, {'from': deployer})
    cburner = CBurner.deploy(underlying_burner, RECOVERY, OWNER_ADMIN, EMERGENCY_ADMIN, {'from': deployer})
    yburner = YBurner.deploy(underlying_burner, RECOVERY, OWNER_ADMIN, EMERGENCY_ADMIN, {'from': deployer})

    # for LP burner we retain initial ownership to set it up
    lp_burner = LPBurner.deploy(RECOVERY, deployer, EMERGENCY_ADMIN, {'from': deployer})

    # set LP burner to unwrap sbtcCRV -> sBTC and transfer to BTC burner
    lp_burner.set_swap_data(
        "0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3",
        "0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6",
        btc_burner,
        {'from': deployer}
    )

    # this ownership transfer must be accepted by the DAO
    lp_burner.commit_transfer_ownership(OWNER_ADMIN, {'from': deployer})

    # set the burners within pool proxy
    to_set = [(k[-1], x) for k, v in BURNERS.items() for x in v]
    burners = [i[0] for i in to_set] + [ZERO_ADDRESS] * (40-len(to_set))
    coins = [i[1] for i in to_set] + [ZERO_ADDRESS] * (40-len(to_set))

    proxy.set_many_burners(coins[:20], burners[:20], {'from': deployer})
    proxy.set_many_burners(coins[20:], burners[20:], {'from': deployer})
    proxy.set_burner(lp_tripool, distributor, {'from': deployer})

    # approve USDN burner to donate to USDN pool
    proxy.set_donate_approval(
        "0x0f9cb53Ebe405d49A0bbdBD291A65Ff571bC83e1",
        usdn_burner,
        True,
        {'from': deployer}
    )

    # set PoolProxy ownership
    proxy.commit_set_admins(OWNER_ADMIN, PARAM_ADMIN, EMERGENCY_ADMIN, {'from': deployer})
    proxy.apply_set_admins({'from': deployer})

    print(f"Success! Gas used: {initial_balance - deployer.balance()/1e18:.4f} ETH")
