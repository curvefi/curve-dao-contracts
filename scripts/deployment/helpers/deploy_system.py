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
                "lix": lix.address,
                "registry": registry.address,
                "escrow": staking_system.escrow.address,
                "fee_distributor": staking_system.fee_distributor.address,
                "gauge_controller": staking_system.gauge_controller.address,
                "lix_distributor": staking_system.lix_distributor.address,
            },
            indent=2,
        )
    )
    f.close()
    return staking_system