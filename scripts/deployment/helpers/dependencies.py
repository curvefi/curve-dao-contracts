from ..StakingSystem import get_accounts
from brownie import (
    ERC20,
)



def load_dependencies():
    print('TODO')


def deploy_dependencies():
    accounts = get_accounts()
    return ERC20.deploy("Lixir Token", "LIX", 18, 10000000 * 10 ** 18, {"from": accounts[3]})
