import requests

from brownie import Contract, chain
from brownie.convert import to_address

# This script is used to simulate an arbitrary ownership vote (where the
# transaction is executed via 0x40907540d8a6c65c637785e8f8b742ae6b0b9968).

# contract to be called when the vote is executed
TARGET = ""

# calldata to use when calling `TARGET`
CALLDATA = "0x"

# metadata description to include with vote
# ipfs content should be in the form `{"text":"a description of the vote"}`
# you can use https://ipfsbrowser.com/ to pin the description file to IPFS
DESCRIPTION = "ipfs:[IPFS HASH HERE]"


def main():
    voting_escrow = Contract("0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2")
    aragon = Contract("0xe478de485ad2fe566d49342cbd03e49ed7db3356")
    agent = Contract("0x40907540d8a6c65c637785e8f8b742ae6b0b9968")

    # fetch the top veCRV holders so we can pass the vote
    data = requests.get(
        f"https://api.ethplorer.io/getTopTokenHolders/{voting_escrow}",
        params={'apiKey': "freekey", 'limit': 50},
    ).json()['holders'][::-1]

    # vote needs 30% to reach qurom, we'll vote with 35% in case
    # there's been some decay since ethplorer pulled their data
    holders = []
    weight = 0
    while weight < 35:
        row = data.pop()
        holders.append(to_address(row['address']))
        weight += row['share']

    # prepare the evm calldata for the vote
    agent_calldata = agent.execute.encode_input(TARGET, 0, CALLDATA)[2:]
    length = hex(len(agent_calldata)//2)[2:].zfill(8)
    evm_script = f"0x0000000140907540d8a6c65c637785e8f8b742ae6b0b9968{length}{agent_calldata}"

    # create the new vote
    tx = aragon.newVote(evm_script, DESCRIPTION, False, False, {'from': holders[0]})
    vote_id = tx.events['StartVote']['voteId']

    # vote
    for acct in holders:
        aragon.vote(vote_id, True, False, {'from': acct})

    # sleep for a week so it has time to pass
    chain.sleep(86400*7)

    # moment of truth - execute the vote!
    aragon.executeVote(vote_id, {'from': holders[0]})

    print(f"Success!\n\nEVM script for vote: {evm_script}")
