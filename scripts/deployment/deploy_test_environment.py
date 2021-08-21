from .helpers.dependencies import deploy_dependencies
from .helpers.vault_helpers import deploy_test_vaults

def main():
    deploy_dependencies() # deploy LIX
    deploy_test_vaults() # deploy vaults
    # deploy_system()
