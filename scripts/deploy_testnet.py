# Testnet deployment script

import json
from web3 import middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy as gas_strategy
from brownie import web3, accounts, ERC20CRV, VotingEscrow, ERC20, ERC20LP, CurvePool, Registry

USE_STRATEGIES = False  # Needed for the ganache-cli tester which doesn't like middlewares
POA = True

DEPLOYER = "0x66aB6D9362d4F35596279692F0251Db635165871"
TOKEN_MANAGER = "0x941A4d37eaC4fA7d4A2Bc68a2c8eA3a760D19039"
ARAGON_AGENT = "0x0063046686E46Dc6F15918b61AE2B121458534a5"

DISTRIBUTION_AMOUNT = 10 ** 6 * 10 ** 18
DISTRIBUTION_ADDRESSES = ["0x33A4622B82D4c04a53e170c638B944ce27cffce3", "0x6cd85bbb9147b86201d882ae1068c67286855211"]

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def repeat(f, *args):
    """
    Repeat when geth is not broadcasting (unaccounted error)
    """
    while True:
        try:
            return f(*args)
        except KeyError:
            continue


def save_abi(contract, name):
    with open('%s.abi' % name, 'w') as f:
        json.dump(contract.abi, f)


def deploy_erc20s_and_pool(deployer):
    coin_a = repeat(ERC20.deploy, "Coin A", "USDA", 18, {'from': deployer})
    repeat(coin_a._mint_for_testing, 10 ** 9 * 10 ** 18, {'from': deployer})
    coin_b = repeat(ERC20.deploy, "Coin B", "USDB", 18, {'from': deployer})
    repeat(coin_b._mint_for_testing, 10 ** 9 * 10 ** 18, {'from': deployer})

    lp_token = repeat(ERC20LP.deploy, "Some pool", "cPool", 18, 0, {'from': deployer})
    save_abi(lp_token, 'lp_token')
    pool = repeat(CurvePool.deploy, [coin_a, coin_b], lp_token, 100, 4 * 10 ** 6, {'from': deployer})
    save_abi(pool, 'curve_pool')
    repeat(lp_token.set_minter, pool, {'from': deployer})

    registry = repeat(Registry.deploy, [ZERO_ADDRESS] * 4, {'from': deployer})
    save_abi(registry, 'registry')

    for account in DISTRIBUTION_ADDRESSES:
        repeat(coin_a.transfer, account, DISTRIBUTION_AMOUNT, {'from': deployer})
        repeat(coin_b.transfer, account, DISTRIBUTION_AMOUNT, {'from': deployer})

    repeat(pool.commit_transfer_ownership, ARAGON_AGENT, {'from': deployer})
    repeat(pool.apply_transfer_ownership, {'from': deployer})

    repeat(registry.commit_transfer_ownership, ARAGON_AGENT, {'from': deployer})
    repeat(registry.apply_transfer_ownership, {'from': deployer})

    return pool, registry


def main():
    if USE_STRATEGIES:
        web3.eth.setGasPriceStrategy(gas_strategy)
        web3.middleware_onion.add(middleware.time_based_cache_middleware)
        web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
        web3.middleware_onion.add(middleware.simple_cache_middleware)
        if POA:
            web3.middleware_onion.inject(middleware.geth_poa_middleware, layer=0)

    deployer = accounts.at(DEPLOYER)

    deploy_erc20s_and_pool(deployer)

    token = repeat(ERC20CRV.deploy, "Curve DAO Token", "CRV", 18, 10 ** 9, {'from': deployer})
    save_abi(token, 'token_crv')

    escrow = repeat(VotingEscrow.deploy, token, {'from': deployer})
    save_abi(escrow, 'voting_escrow')

    repeat(escrow.changeController, TOKEN_MANAGER, {'from': deployer})

    for account in DISTRIBUTION_ADDRESSES:
        repeat(token.transfer, account, DISTRIBUTION_AMOUNT, {'from': deployer})
