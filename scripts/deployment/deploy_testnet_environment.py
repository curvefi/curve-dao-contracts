from .helpers.vault_helpers import deploy_test_vaults
from .helpers.deploy_system import deploy_system
from .deploy_gauges import deploy_gauges

def main():
    deploy_system() # escrow, fee_dist, lix_dist, gauge controller
    deploy_gauges() # gauges