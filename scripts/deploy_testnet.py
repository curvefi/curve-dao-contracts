# Testnet deployment script

from brownie import accounts, ERC20CRV, VotingEscrow
import json

POA = True

DEPLOYER = "0x66aB6D9362d4F35596279692F0251Db635165871"
TOKEN_MANAGER = "0x941A4d37eaC4fA7d4A2Bc68a2c8eA3a760D19039"

DISTRIBUTION_AMOUNT = 10 ** 6 * 10 ** 18
DISTRIBUTION_ADDRESSES = ["0x33A4622B82D4c04a53e170c638B944ce27cffce3", "0x6cd85bbb9147b86201d882ae1068c67286855211"]


def main():
    deployer = accounts.at(DEPLOYER)

    print("Deploying CRV token...")
    token = ERC20CRV.deploy("Curve DAO Token", "CRV", 18, 10 ** 9, {'from': deployer})
    with open('token_crv.abi', 'w') as f:
        json.dump(token.abi, f)

    print("Deploying voting escrow...")
    escrow = VotingEscrow.deploy(token, {'from': deployer})
    with open('voting_escrow.abi', 'w') as f:
        json.dump(escrow.abi, f)

    print("Changing controller...")
    escrow.changeController(TOKEN_MANAGER, {'from': deployer})

    print("Sending coins...")
    for account in DISTRIBUTION_ADDRESSES:
        token.transfer(DEPLOYER, DISTRIBUTION_AMOUNT, {'from': account})
