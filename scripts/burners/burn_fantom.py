import sys

from brownie import ZERO_ADDRESS, Contract, PoolProxySidechain, accounts


def _get_pool_list():
    sys.stdout.write("Getting list of pools and coins from registry...")
    sys.stdout.flush()

    provider = Contract("0x0000000022D53366457F9d5E68Ec105046FC4383")
    registry = Contract(provider.get_registry())

    pool_count = registry.pool_count()
    pool_list = []
    coin_list = set()
    for i in range(pool_count):
        sys.stdout.write(f"\rGetting list of pools and coins from registry ({i+1}/{pool_count})...")
        sys.stdout.flush()
        swap = Contract(registry.pool_list(i))
        pool_list.append(swap)
        coin_list.update([i for i in registry.get_coins(swap) if i != ZERO_ADDRESS])

    print()
    return pool_list, coin_list


def main():
    acct = accounts.load("curve-deploy")

    proxy = PoolProxySidechain.at("0xffbACcE0CC7C19d46132f1258FC16CF6871D153c")
    usdt = Contract("0x049d68029688eabf473097a2fc38ef61633a3c7a")

    pool_list, coin_list = _get_pool_list()

    while pool_list:
        to_claim = pool_list[:20]
        pool_list = pool_list[20:]
        if len(to_claim) < 20:
            to_claim += [ZERO_ADDRESS] * (20 - len(to_claim))
        proxy.withdraw_many(to_claim, {"from": acct})

    coin_list.remove(usdt.address)
    coin_list.add("0x58e57ca18b7a47112b877e31929798cd3d703b0f")  # tricrypto
    coin_list = list(coin_list)

    to_burn = []
    while coin_list:
        coin = Contract(coin_list.pop())
        if coin.balanceOf(proxy) == 0:
            continue
        to_burn.append(coin)
        to_burn_padded = to_burn + [ZERO_ADDRESS] * (20 - len(to_burn))
        if not coin_list or proxy.burn_many.estimate_gas(to_burn_padded, {"from": acct}) >= 4000000:
            proxy.burn_many(to_burn_padded, {"from": acct})
            to_burn.clear()

    proxy.bridge(usdt, {"from": acct})
