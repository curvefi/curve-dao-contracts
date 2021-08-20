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

WEEK = 86400 * 7

class VeLixSystem:
    def __init__(self, lixir_accounts, dep_config, system_config):
        self.lix = dep_config.lix
        self.deployer = lixir_accounts.deployer
    
    @classmethod
    def deploy(cls, lix, vaults, lixir_accounts):
        admin, emergency_return, deployer = lixir_accounts
        escrow = VotingEscrow.deploy(lix, "Vote-escrowed LIX", "veLIX", "veLIX_0.99", {"from": deployer})

        start_time = escrow.tx.timestamp + WEEK # TODO: check this
        # we could automatically get funds in the FeeDistributor by using a VaultProxy and a bunch of burners
        # or we can just manually burn and transfer. We are doing the latter until later notice (progessively decentralizing)
        feeDistributor = FeeDistributor.deploy(escrow, start_time, lix, admin, emergency_return, {"from": deployer})
        gauge_controller = GaugeController.deploy(lix, escrow, {"from": deployer}) # from admin?
        distributor = LixDistributor.deploy(lix, gauge_controller, {"from": deployer})
        
        for vault in vaults:
            vault_gauge = VaultGauge.deploy(vault, distributor, deployer, {"from": deployer})

        # config
        lix.approve(distributor, 6000000, {"from": deployer})
        distributor.set_initial_params(6000000, {"from": deployer})
        gauge_controller.add_type(b"Liquidity", {"from": deployer})
        gauge_controller.change_type_weight(0, 10 ** 18, {"from": deployer}) # we only need one type and can weight it as 1.
        gauge_controller.add_gauge(vault_gauge, 0, 10 ** 18, {"from": deployer})
