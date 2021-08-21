from collections import namedtuple
from brownie import (
    GaugeController,
    VaultGauge,
    LixirVault,
    LixirRegistry,
    LixDistributor,
    VotingEscrow,
    FeeDistributor,
    accounts,
    chain,
    web3,
)
from .helpers.chain_to_name import chain_to_name

StakingDependenciesConfig = namedtuple("LixirDependenciesConfig", ["lix", "registry"])

StakingSystemConfig = namedtuple(
    "StakingSystemConfig",
    [
        "escrow",
        "fee_distributor",
        "gauge_controller",
        "lix_distributor",
    ],
)

StakingAccounts = namedtuple(
    "LixirAccounts",
    ["fee_dist_admin", "gauge_admin", "emergency_return", "deployer"],
)

class StakingSystem:
    __create_key = object()

    def __init__(
        self,
        staking_accounts: StakingAccounts,
        dep_config: StakingDependenciesConfig,
        system_config: StakingSystemConfig
    ):
        # dep_config
        # idk if we need self.registry = dep_config.registry
        self.lix = dep_config.lix
        
        # accounts
        self.admin = staking_accounts.admin
        self.emergency_return = staking_accounts.emergency_return
        self.deployer = staking_accounts.deployer

        # system config
        self.escrow = system_config.escrow
        self.fee_distributor = system_config.fee_distributor
        self.gauge_controller = system_config.gauge_controller
        self.lix_distributor = system_config.lix_distributor


    def deploy_gauge(self, lp_token, ):
        return VaultGauge.deploy(lp_token, self.lix_distributor, self.gauge_admin, {"from": self.deployer, "gas": 2000000})


    @classmethod
    def deploy(cls, lix, registry, staking_accounts: StakingAccounts):
        deployer, fee_dist_admin, emergency_return, gauge_admin = staking_accounts

        escrow = VotingEscrow.deploy(lix, "Vote-escrowed LIX", "veLIX", "veLIX_0.99", {"from": deployer})
        fee_distributor = FeeDistributor.deploy(escrow, 0, lix, fee_dist_admin, emergency_return, {"from": deployer})
        gauge_controller = GaugeController.deploy(lix, escrow, {"from": deployer})
        lix_distributor = LixDistributor.deploy(lix, gauge_controller, {"from": deployer}) # should I 
        
        gauge_controller.add_type(b"Liquidity", {"from": deployer})
        gauge_controller.change_type_weight(0, 10 ** 18, {"from": deployer})
        # lix.approve(distributor, 6000000, {"from": deployer})
        # distributor.set_initial_params(6000000, {"from": deployer})
        dep_config = StakingDependenciesConfig(lix, registry)
        staking_config = StakingSystemConfig(
            escrow,
            fee_distributor,
            gauge_controller,
            lix_distributor
        )

        return StakingSystem(cls.__create_key, staking_accounts, dep_config, staking_config)

def get_accounts():
    network = chain_to_name[chain.id]
    if network == "ganache":
            return StakingAccounts(
                accounts[0],
                accounts[1],
                accounts[2],
                accounts[3],
            )
    f = open(f"deploy_config_{network}.json", "r")
    deploy_config = json.loads(f.read())
    f.close()
    fee_dist_admin = deploy_config["fee_dist_admin"]
    gauge_admin = deploy_config["gauge_admin"]
    emergency_return = deploy_config["emergency_return"]
    deployer = deploy_config["deployer"]
    return StakingAccounts(fee_dist_admin, gauge_admin, emergency_return, deployer)

