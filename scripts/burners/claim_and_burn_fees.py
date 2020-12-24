import requests
import sys
import time
import warnings

from brownie import Contract, ETH_ADDRESS, ZERO_ADDRESS, accounts
from brownie.network.gas.strategies import GasNowScalingStrategy

warnings.filterwarnings("ignore")

# This script is used to claim fees from all pool contracts
# and "burn" them, converting to 3CRV and sending it to the
# fee distributor to be claimed by veCRV holders. All of the
# transactions within the script may be executed by any account
# at any time.

# the account you wish to perform transactions from
CALLER = accounts.add()

# minimum amount in USD required in order to claim fees from a pool
CLAIM_THRESHOLD = 1000

# fee coins, organized by the fee burner they are handled with
COINS = [
    # LP Burner - for withdrawing LP tokens
    # this burner is called first, as it forwards into other burners
    "0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3",  # sbtcCRV

    # BTC burner, converts to USDC and sends to underlying burner
    "0xeb4c2781e4eba804ce9a9803c67d0893436bb27d",  # renBTC
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # wBTC
    "0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6",  # sBTC
    "0x0316EB71485b0Ab14103307bf65a021042c6d380",  # hBTC
    "0x8dAEBADE922dF735c38C80C7eBD708Af50815fAa",  # tBTC
    "0x5228a22e72ccC52d415EcFd199F99D0665E7733b",  # pBTC
    "0x9be89d2a4cd102d8fecc6bf9da793be995c22541",  # bBTC
    "0x8064d9Ae6cDf087b1bcd5BDf3531bD5d8C537a68",  # oBTC

    # ETH burner, converts to USDC and sends to underlying burner
    "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",  # ETH
    "0x5e74C9036fb86BD7eCdcb084a0673EFc32eA31cb",  # sETH

    # Euro burner, converts to USDC and sends to underlying burner
    "0xdB25f211AB05b1c97D595516F45794528a807ad8",  # EURS
    "0xD71eCFF9342A5Ced620049e616c5035F1dB98620",  # sEUR

    # idleBurner, unwraps and sends to underlying burner
    "0x3fe7940616e5bc47b0775a0dccf6237893353bb4",  # idleDAI
    "0x5274891bEC421B39D23760c04A6755eCB444797C",  # idleUSDC
    "0xF34842d05A1c888Ca02769A633DF37177415C2f8",  # idleUSDT

    # aToken burner, unwraps and sends to underlying burner
    "0x028171bCA77440897B824Ca71D1c56caC55b68A3",  # aDAI
    "0xBcca60bB61934080951369a648Fb03DF4F96263C",  # aUSDC
    "0x3Ed3B47Dd13EC9a98b44e6204A523E766B225811",  # aUSDT

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
    "0xa47c8bf37f92aBed4A126BDA807A7b7498661acD",  # UST

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

# for synth burners, executing converts sUSD to USDC and forwards to
# underlying burner. this has to happen in a separate transaction due
# to the three minute settlement time.
SYNTH_BURNERS = [
    "0x00702BbDEaD24C40647f235F15971dB0867F6bdB",  # BtcBurner
    "0x02C57fedb33D89e12CF6C482CD2D17481A60E311",  # EthBurner
    "0x3a16b6001201577CC67bDD8aAE5A105bbB035882",  # EuroBurner
]


_rate_cache = {}
gas_strategy = GasNowScalingStrategy(initial_speed="standard", max_speed="fast")


def _get_pool_list():
    sys.stdout.write("Getting list of pools from registry...")
    sys.stdout.flush()

    provider = Contract("0x0000000022D53366457F9d5E68Ec105046FC4383")
    registry = Contract(provider.get_registry())

    pool_count = registry.pool_count()
    pool_list = []
    for i in range(pool_count):
        sys.stdout.write(f"\rGetting list of pools from registry ({i+1}/{pool_count})...")
        sys.stdout.flush()
        pool_list.append(Contract(registry.pool_list(i)))

    print()
    return pool_list


def _fetch_rate(address):
    # fetch the current rate for a coin from coingecko
    address = str(address).lower()
    if address not in _rate_cache:
        _rate_cache[address] = requests.get(
            "https://api.coingecko.com/api/v3/simple/token_price/ethereum",
            params={'contract_addresses': address, 'vs_currencies': "usd"}
        ).json()[address]['usd']

    return _rate_cache[address]


def _get_admin_balances(pool):
    admin_balances = []

    for i in range(8):
        try:
            coin = Contract(pool.coins(i))
            if hasattr(pool, "admin_balances"):
                balance = pool.admin_balances(i)
            else:
                balance = coin.balanceOf(pool) - pool.balances(i)
            balance = balance / 10**coin.decimals() * _fetch_rate(coin)
            admin_balances.append(balance)

        except Exception:
            return admin_balances


def get_pending():
    pool_list = _get_pool_list()
    pending = {}
    for i, pool in enumerate(pool_list, start=1):
        sys.stdout.write(f"\rQuerying pending fee amounts ({i}/{len(pool_list)})...")
        sys.stdout.flush()
        pending[pool] = sum(_get_admin_balances(pool))

    print()
    for addr, value in sorted(pending.items(), key=lambda k: k[1], reverse=True):
        print(f"{addr}: ${value:,.2f}")

    print(f'\nTotal pending claimable amount: ${sum(pending.values()):,.2f} USD')

    return pending


def main(acct=CALLER, claim_threshold=CLAIM_THRESHOLD):
    lp_tripool = Contract("0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490")
    distributor = Contract("0xA464e6DCda8AC41e03616F95f4BC98a13b8922Dc")
    proxy = Contract("0xeCb456EA5365865EbAb8a2661B0c503410e9B347")

    initial_balance = lp_tripool.balanceOf(distributor)

    # get list of active pools
    pool_list = _get_pool_list()

    # withdraw pool fees to pool proxy
    to_claim = []
    for i in range(len(pool_list)):

        # check claimable amount
        sys.stdout.write(f"\rQuerying pending fee amounts ({i}/{len(pool_list)})...")
        sys.stdout.flush()
        claimable = _get_admin_balances(pool_list[i])
        if sum(claimable) >= claim_threshold:
            to_claim.append(pool_list[i])

        if i == len(pool_list) - 1 or len(to_claim) == 20:
            to_claim += [ZERO_ADDRESS] * (20-len(to_claim))
            proxy.withdraw_many(to_claim, {'from': acct, 'gas_price': gas_strategy})
            to_claim = []

    # call burners to convert fee tokens to 3CRV
    burn_start = 0
    to_burn = []
    for i in range(len(COINS)):
        # no point in burning if we have a zero balance
        if COINS[i] == ETH_ADDRESS:
            if proxy.balance() > 0:
                to_burn.append(COINS[i])
        elif Contract(COINS[i]).balanceOf(proxy) > 0:
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
    time.sleep(max(burn_start + 180 - time.time(), 0))

    # call `execute` on synth burners that require it
    # converts settled sUSD to USDC and sends to the underlying burner
    susd = Contract("0x57Ab1ec28D129707052df4dF418D58a2D46d5f51")
    for burner in SYNTH_BURNERS:
        if susd.balanceOf(burner) > 0:
            Contract(burner).execute({'from': acct, 'gas_price': gas_strategy})

    # call `execute` on the underlying burner
    # deposits DAI/USDC/USDT into 3pool and transfers the 3CRV to the fee distributor
    underlying_burner = Contract("0x874210cF3dC563B98c137927e7C951491A2e9AF3")
    underlying_burner.execute({'from': acct, 'gas_price': gas_strategy})

    # finally, call to burn 3CRV - this also triggers a token checkpoint
    proxy.burn(lp_tripool, {'from': acct, 'gas_price': gas_strategy})

    final = lp_tripool.balanceOf(distributor)
    print(f"Success! Total 3CRV fowarded to distributor: {(final-initial_balance)/1e18:.4f}")
