# Testnet deployment script

from brownie import accounts, ERC20CRV, VotingEscrow
import json

ACCOUNT = 1
TOKEN_MANAGER = "0x941A4d37eaC4fA7d4A2Bc68a2c8eA3a760D19039"
ADDR2 = "0x6cd85bbb9147b86201d882ae1068c67286855211"


def main():
    account = accounts[ACCOUNT]
    print("Deploying with:", account.address, '\n')
    token = ERC20CRV.deploy("Curve DAO Token", "CRV", 18, 10 ** 9, {'from': account})
    escrow = VotingEscrow.deploy(token, {'from': account})
    with open('token_crv.abi', 'w') as f:
        json.dump(token.abi, f)
    with open('voting_escrow.abi', 'w') as f:
        json.dump(escrow.abi, f)
    print("Changing controller...")
    escrow.changeController(TOKEN_MANAGER, {'from': account})
    print("Sending coins...")
    token.transfer(ADDR2, 500 * 10 ** 6 * 10 ** 18, {'from': account})
