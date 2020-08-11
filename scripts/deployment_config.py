"""
Deployment Configuration file
=============================
This script holds customizeable / sensetive values related to the DAO deployment scripts.
See `README.md` in this directory for more information on how deployment works.
"""

from brownie import accounts, rpc, web3
from web3 import middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy as gas_strategy

LP_VESTING_JSON = "lp-vesting-percents.json"
DEPLOYMENTS_JSON = "deployments.json"
REQUIRED_CONFIRMATIONS = 3

# Aragon agent address - set after the Aragon DAO is deployed
ARAGON_AGENT = None


# `VestingEscrow` contracts to be deployed
STANDARD_ESCROWS = [
    # {
    #     'duration': YEAR * 2,  # given in seconds
    #     'can_disable': False,
    #     'recipients': {},  # dict of {"address": amount as integer (1 token is 10**18) }
    #     'admin': "0x00",  # OPTIONAL new admin address, set AFTER funding completes
    # },
    # {
    #     'duration': YEAR * 4,
    #     'can_disable': False,
    #     'recipients': {}
    # },
]

# `VestingEscrowFactory` contracts to be deployed
FACTORY_ESCROWS = [
    # {
    #     'admin': "0x00",
    #     'amount': 0
    # }
]


def get_live_admin():
    # Admin and funding admin account objects used for in a live environment
    # May be created via accounts.load(name) or accounts.add(privkey)
    # https://eth-brownie.readthedocs.io/en/stable/account-management.html
    admin = None  #
    funding_admins = [None, None, None, None]
    return admin, funding_admins


if not rpc.is_active():
    # logic that only executes in a live environment
    web3.eth.setGasPriceStrategy(gas_strategy)
    web3.middleware_onion.add(middleware.time_based_cache_middleware)
    web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
    web3.middleware_onion.add(middleware.simple_cache_middleware)
