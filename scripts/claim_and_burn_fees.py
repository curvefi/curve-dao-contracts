import time
from brownie import Contract, ZERO_ADDRESS, accounts
from brownie.network.gas.strategies import GasNowScalingStrategy

# This script is used to claim fees from all pool contracts
# and "burn" them, converting to 3CRV and sending it to the
# fee distributor to be claimed by veCRV holders. All of the
# transactions within the script may be executed by any account
# at any time.

# the account you wish to perform transactions from
CALLER = accounts.add()

gas_strategy = GasNowScalingStrategy(initial_speed="standard", max_speed="fast")

# fee coins, organized by the fee burner they are handled with
COINS = [
    # LP Burner - for withdrawing LP tokens
    # this burner is called first, as it forwards into other burners
    "0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3",  # sbtcCRV

    # BTC burner, convers to USDC and sends to underlying burner
    "0xeb4c2781e4eba804ce9a9803c67d0893436bb27d",  # renBTC
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # wBTC
    "0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6",  # sBTC
    "0x0316EB71485b0Ab14103307bf65a021042c6d380",  # hBTC
    "0x8dAEBADE922dF735c38C80C7eBD708Af50815fAa",  # tBTC

    # cToken burner, unwraps and sends to underlying burner
    "0x39aa39c021dfbae8fac545936693ac917d5e7563",  # cDAI
    "0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",  # cUSDC

    # yToken burner, unwraps and sends to underlying burner
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

    # meta-burner, for assets that can be directly swapped to 3CRV
    "0x056fd409e1d7a124bd7017459dfea2f387b6d5cd",  # GUSD
    "0xdf574c24545e5ffecb9a659c229253d4111d87e1",  # HUSD
    "0x1c48f86ae57291f7686349f12601910bd8d470bb",  # USDK
    "0x0E2EC54fC0B509F445631Bf4b91AB8168230C752",  # LinkUSD
    "0xe2f2a5C287993345a840Db3B0845fbC70f5935a5",  # MUSD
    "0x196f4727526eA7FB1e17b2071B3d8eAA38486988",  # RSV
    "0x5bc25f649fc4e26069ddf4cf4010f9f706c23831",  # DUSD

    # USDN burner
    "0x674C6Ad92Fd080e4004b2312b45f796a192D27a0",  # USDN

    # underlying burner
    # called last, as other burners forward to it
    "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
    "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
    "0x8e870d67f660d95d5be530380d0ec0bd388289e1",  # PAX
    "0x57ab1ec28d129707052df4df418d58a2d46d5f51",  # sUSD
]


def main(acct=CALLER):
    lp_tripool = Contract("0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490")
    distributor = Contract("0xA464e6DCda8AC41e03616F95f4BC98a13b8922Dc")
    proxy = Contract("0xeCb456EA5365865EbAb8a2661B0c503410e9B347")
    btc_burner = Contract("0x00702BbDEaD24C40647f235F15971dB0867F6bdB")
    underlying_burner = Contract("0x874210cF3dC563B98c137927e7C951491A2e9AF3")

    initial_balance = lp_tripool.balanceOf(distributor)

    # get list of active pools
    provider = Contract("0x0000000022D53366457F9d5E68Ec105046FC4383")
    registry = Contract(provider.get_registry())
    pool_list = [Contract(registry.pool_list(i)) for i in range(registry.pool_count())]

    # withdraw pool fees to pool proxy
    for i in range(0, len(pool_list), 20):
        pools = pool_list[i:i+20]
        pools += [ZERO_ADDRESS] * (20-len(pools))
        proxy.withdraw_many(pools, {'from': acct, 'gas_price': gas_strategy})

    # call burners to convert fee tokens to 3CRV
    burn_start = 0
    to_burn = []
    for i in range(len(COINS)):
        to_burn.append(COINS[i])
        to_burn_padded = to_burn + [ZERO_ADDRESS] * (20-len(to_burn))

        # estimate gas to decide when to burn - some of the burners are gas guzzlers
        if i == len(COINS) - 1 or proxy.burn_many.estimate_gas(to_burn_padded, {'from': acct}) > 2000000:
            tx = proxy.burn_many(to_burn_padded, {'from': acct, 'gas_price': gas_strategy})
            to_burn = []
            if not burn_start:
                # record the timestamp of the first tx - need to
                # know how long to wait to finalize synth swaps
                burn_start = tx.timestamp

    # wait on synths to finalize
    time.sleep(burn_start + 180 - time.time())

    # call `execute` on burners
    # for btc burner, this converts sUSD to USDC and sends to the underlying burner
    btc_burner.execute({'from': acct, 'gas_price': gas_strategy})
    # for underlying burner, this deposits USDC/USDT/DAI into 3CRV and sends to the distributor
    underlying_burner.execute({'from': acct, 'gas_price': gas_strategy})

    # finally, call to burn 3CRV - this also triggers a token checkpoint
    proxy.burn(lp_tripool, {'from': acct, 'gas_price': gas_strategy})

    final = lp_tripool.balanceOf(distributor)
    print(f"Success! Total 3CRV fowarded to distributor: {final-initial_balance/1e18:.4f}")
