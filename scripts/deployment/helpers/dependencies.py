import json
from ..StakingSystem import get_accounts
from brownie import (
    ERC20,
    LixirRegistry
)



def load_dependencies():
    print('TODO')


def deploy_dependencies():
    accounts = get_accounts()
    registry = LixirRegistry.deploy(accounts[0], accounts[0], accounts[0], accounts[0], {"from": accounts.deployer})
    token = ERC20.deploy("Lixir Token", "LIX", 18, 10000000 * 10 ** 18, {"from": accounts.deployer})
    f = open("deployed/ganache_dependencies.json", "w")
    f.write(
        json.dumps(
            {
                "registry": registry.address,
                "lix": token.address,
            },
            indent=2,
        )
    )
    f.close()
    return (
        registry,
        token,
    )
