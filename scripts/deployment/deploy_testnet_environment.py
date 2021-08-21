from brownie import chain

chain_to_name = {5: "goerli", 1337: "ganache", 4: 'rinkeby', 1: 'mainnet'}


def deploy_gauges():
    network = chain_to_name[chain.id]


def main():
    # retrieve_vaults()
    # deploy_system()
    # deploy_gauges()