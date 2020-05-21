from brownie import accounts, ERC20CRV, VotingEscrow
import json

ACCOUNT = 1


def main():
    account = accounts[ACCOUNT]
    print("Deploying with:", account.address, '\n')
    token = ERC20CRV.deploy("Curve DAO Token", "CRV", 18, 10 ** 9, {'from': account})
    escrow = VotingEscrow.deploy(token, {'from': account})
    with open('token_crv.abi', 'w') as f:
        json.dump(token.abi, f)
    with open('voting_escrow.abi', 'w') as f:
        json.dump(escrow.abi, f)
