from brownie import ERC20, LixirVault, accounts, chain
from .chain_to_name import chain_to_name
import json
# from scripts.helpers.imports import IERC20
# from lixir.system import VaultDeployParameters

# base_params = {
#     "strategy": {
#         "type": "simple_gwap",
#         "fee": 3000,
#         "tick_short_duration": 60,
#         "max_tick_diff": 180,
#         "main_spread": 1800,
#         "range_spread": 900,
#     }
# }

tokenPairs = [
    (("USD Tether", "USDT"), ("USD Coin", "USDC")),
    (("USD Coin", "USDC"), ("Wrapped Bitcoin", "WBTC")),
    (("renVM Bitcoin", "renBTC"), ("Wrapped Bitcoin", "WBTC")),
]


tokenSet = set(v for w in tokenPairs for v in w)
print('token set', tokenSet)

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
    

# def config_to_args(config):
#     assert config["strategy"]["type"] == "simple_gwap"
#     assert len(config["tokens"]) == 2
#     return VaultDeployParameters(
#         config["name"],
#         config["symbol"],
#         IERC20(config["tokens"][0]),
#         IERC20(config["tokens"][1]),
#         config["strategy"]["fee"],
#         config["strategy"]["tick_short_duration"],
#         config["strategy"]["max_tick_diff"],
#         config["strategy"]["main_spread"],
#         config["strategy"]["range_spread"],
#     )

 