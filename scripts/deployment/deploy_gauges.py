from brownie import chain
import json
import os
from datetime import datetime
from .helpers.chain_to_name import chain_to_name
from .StakingSystem import StakingSystem, get_accounts

def deploy_gauges():
    network = chain_to_name[chain.id]
    lixir_accounts = get_accounts()
    system = StakingSystem.load(
        lixir_accounts,
        f"deployed/{network}_dependencies.json",
        f"deployed/{network}_system.json",
    )

    f = open(f"deployed/{network}_vaults.json", "r")
    vaults = json.loads(f.read())
    f.close()

    gauge_addresses = {}
    gauges = []

    for vault in vaults:
        gauge = system.deploy_gauge(vaults[vault])
        gauges.append(gauge)
        gauge_addresses[vault] = {"vault": vaults[vault], "gauge": gauge.address}

    f = open(
        f"deployed/{network}_gauges_deployed_{datetime.utcnow().isoformat()}.json", "w"
    )
    f.write(json.dumps(gauge_addresses, indent=2))
    f.close()
    
    if os.path.isfile(f"deployed/{network}_gauges_deployed.json"):
        f = open(f"deployed/{network}_gauges_deployed.json", "r")
        last_addresses = json.loads(f.read())
        f.close()
    else:
        last_addresses = {}
    gauges_addresses = {**last_addresses, **gauge_addresses}
    f = open(f"deployed/{network}_gauges_deployed.json", "w")
    f.write(json.dumps(gauges_addresses, indent=2))
    f.close()
    return gauges

def main():
    deploy_gauges()