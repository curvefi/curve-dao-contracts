from brownie import ERC20, LixirVault, accounts, chain
from .chain_to_name import chain_to_name
import json


tokenPairs = [
    (("USD Tether", "USDT"), ("USD Coin", "USDC")),
    (("USD Coin", "USDC"), ("Wrapped Bitcoin", "WBTC")),
    (("renVM Bitcoin", "renBTC"), ("Wrapped Bitcoin", "WBTC")),
]

tokenSet = set(v for w in tokenPairs for v in w)


def create_token(name, symbol):
    return ERC20.deploy(name, symbol, 18, 10**21, {"from": accounts[0]})


def deploy_test_vaults():
    network = chain_to_name[chain.id]
    f = open(f"deployed/{network}_dependencies.json", "r")
    dependencies = json.loads(f.read())
    f.close()

    vaults = {}
    tokens = {}
    for token in tokenSet:
        tokens[token[1]] = create_token(token[0], token[1])
    for pair in tokenPairs:
        vault = LixirVault.deploy(dependencies["registry"], {"from": accounts[0]})
        vault.initialize("Test Vault Token", "LVT", tokens[pair[0][1]], tokens[pair[1][1]], accounts[0], accounts[0], accounts[0])
        vaults[pair[0][1] + '-' + pair[1][1]] = vault.address
    
    f = open(f"deployed/{network}_vaults.json", "w")
    f.write(json.dumps(vaults, indent=2))
    f.close()
 