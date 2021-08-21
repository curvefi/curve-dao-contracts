# Testnet deployment script

import json
from operator import truediv
import time

from brownie import (
    ERC20,
    GaugeController,
    VaultGauge,
    LixirVault,
    LixirRegistry,
    LixDistributor,
    VotingEscrow,
    FeeDistributor,
    accounts,
    web3,
)
from web3 import middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy as gas_strategy

USE_STRATEGIES = False  # Needed for the ganache-cli tester which doesn't like middlewares
POA = True

DEPLOYER = "0xFD3DeCC0cF498bb9f54786cb65800599De505706"

DISTRIBUTION_AMOUNT = 10 ** 2 * 10 ** 18
DISTRIBUTION_ADDRESSES = [
    "0x39415255619783A2E71fcF7d8f708A951d92e1b6",
    "0x6cd85bbb9147b86201d882ae1068c67286855211",
]
VESTING_ADDRESSES = ["0x6637e8531d68917f5Ec31D6bA5fc80bDB34d9ef1"]

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

CONFS = 1


def repeat(f, *args):
    """
    Repeat when geth is not broadcasting (unaccounted error)
    """
    while True:
        try:
            return f(*args)
        except KeyError:
            continue

def brownie_deploy_setup(deployer):
    coin_a = ERC20.deploy("Coin A", "USDA", 18, 10 ** 9 * 10 ** 18, {"from": deployer, "required_confs": CONFS})
    coin_b = ERC20.deploy("Coin B", "USDB", 18, 10 ** 9 * 10 ** 18, {"from": deployer, "required_confs": CONFS})

    registry = LixirRegistry.deploy(ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, {"from": deployer, "required_confs": CONFS})

    vault = LixirVault.deploy(registry, {"from": deployer, "required_confs": CONFS})
    vault.initialize("Lixir Vault USDA USDB", "LVT_USDA_USDB", coin_a, coin_b, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, {"from": deployer, "required_confs": CONFS})

    for account in DISTRIBUTION_ADDRESSES:
        coin_a.transfer(
            account,
            DISTRIBUTION_AMOUNT,
            {"from": deployer, "required_confs": CONFS},
        )
        coin_b.transfer(
            account,
            DISTRIBUTION_AMOUNT,
            {"from": deployer, "required_confs": CONFS},
        )

    return [vault, coin_a, coin_b]


def main():
    deployer = accounts.at(DEPLOYER, force=True)
    [lp_token, coin_a, coin_b] = brownie_deploy_setup(deployer)
    lix = ERC20.deploy("Lixir Token", "LIX", 18, 10000000, {"from": deployer, "required_confs": CONFS})
    

    for account in DISTRIBUTION_ADDRESSES:
        lix.transfer(
            account,
            DISTRIBUTION_AMOUNT,
            {"from": deployer, "required_confs": CONFS},
        )


    # deploying new contracts
    escrow = VotingEscrow.deploy(lix, "Vote-escrowed LIX", "veLIX", "veLIX_0.99", {"from": deployer, "required_confs": CONFS})
    
    # we could automatically get funds in the FeeDistributor by using a VaultProxy and a bunch of burners
    # or we can just manually burn and transfer. We are doing the latter until later notice (progessively decentralizing)
    feeDistributor = FeeDistributor.deploy(escrow, 0, lix, ZERO_ADDRESS, deployer, {"from": deployer, "required_confs": CONFS})
    gauge_controller = GaugeController.deploy(lix, escrow, {"from": deployer, "required_confs": CONFS})
    distributor = LixDistributor.deploy(lix, gauge_controller, {"from": deployer, "required_confs": CONFS})
    vault_gauge = VaultGauge.deploy(lp_token, distributor, deployer, {"from": deployer, "required_confs": CONFS})

    # config
    lix.approve(distributor, 6000000, {"from": deployer, "required_confs": CONFS})
    distributor.set_initial_params(6000000, {"from": deployer, "required_confs": CONFS})
    gauge_controller.add_type(b"Liquidity", {"from": deployer, "required_confs": CONFS})
    gauge_controller.change_type_weight(0, 10 ** 18, {"from": deployer, "required_confs": CONFS}) # we only need one type and can weight it as 1.
    gauge_controller.add_gauge(vault_gauge, 0, 10 ** 18, {"from": deployer, "required_confs": CONFS})