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

    proxy = PoolProxySidechain.at("0xd6930b7f661257DA36F93160149b031735237594")
    usdc = Contract("0x2791bca1f2de4661ed88a30c99a7a9449aa84174")

    pool_list, coin_list = _get_pool_list()

    while pool_list:
        to_claim = pool_list[:20]
        pool_list = pool_list[20:]
        if len(to_claim) < 20:
            to_claim += [ZERO_ADDRESS] * (20 - len(to_claim))
        proxy.withdraw_many(to_claim, {"from": acct, "gas_price": "30 gwei"})

    coin_list.discard(usdc.address)
    coin_list.add("0xdAD97F7713Ae9437fa9249920eC8507e5FbB23d3")  # tricrypto3
    coin_list = list(coin_list)

    to_burn = []
    while coin_list:
        coin = Contract(coin_list.pop())
        if coin.balanceOf(proxy) == 0:
            continue
        to_burn.append(coin)
        to_burn_padded = to_burn + [ZERO_ADDRESS] * (20 - len(to_burn))
        if not coin_list or proxy.burn_many.estimate_gas(to_burn_padded, {"from": acct}) >= 4000000:
            proxy.burn_many(to_burn_padded, {"from": acct, "gas_price": "30 gwei"})
            to_burn.clear()

    amount = usdc.balanceOf(proxy)
    tx = proxy.bridge(usdc, {"from": acct, "gas_price": "30 gwei"})
    print(f"Burning phase 1 complete!\nAmount: {amount/1e6:,.2f} USDC\nBridge txid: {tx.txid}")
    print(
        "\nUse `brownie run burners/exit_polygon --network mainnet` to claim on ETH"
        " once the checkpoint is added."
    )
