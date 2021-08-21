from brownie import (
    LixirVault,
    LixirRegistry,
    accounts
)

def deploy_test_vaults():
    LixirRegistry.deploy(accounts[10], accounts[11], accounts[12], accounts[13], {"from": accounts[0]})
    vault = LixirVault.deploy(registry, {"from": accounts[0]})
    vault.initialize("Test Vault Token", "LVT", coin_a, coin_b, accounts[0], accounts[0], accounts[0])
    yield vault