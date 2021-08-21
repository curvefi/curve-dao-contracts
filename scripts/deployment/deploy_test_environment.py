from .helpers.dependencies import deploy_dependencies
from .deploy_test_vaults import deploy_test_vaults

def main():
    deploy_dependencies() # deploy LIX & Vaults
    deploy_test_vaults()
    # deploy_system()
