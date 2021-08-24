from .chain_to_name import chain_to_name
from brownie import chain
from ..StakingSystem import StakingSystem, get_accounts, connect_dependencies, StakingDependenciesConfig
import json


def deploy_system():
    network = chain_to_name[chain.id]
    staking_accounts = get_accounts()
    f = open(f"deployed/{network}_dependencies.json", "r")
    dependencies = json.loads(f.read())
    f.close()
    lix, registry = connect_dependencies(
        StakingDependenciesConfig(dependencies["lix"], dependencies["registry"])
    )
    staking_system = StakingSystem.deploy(lix, registry, staking_accounts)
    f = open(f"deployed/{network}_system.json", "w")
    f.write(
        json.dumps(
            {
                "lix": str(lix),
                "registry": str(registry),
                "escrow": str(staking_system.escrow),
                "fee_distributor": str(staking_system.fee_distributor),
                "gauge_controller": str(staking_system.gauge_controller),
                "lix_distributor": str(staking_system.lix_distributor),
            },
            indent=2,
        )
    )
    f.close()
    return staking_system
