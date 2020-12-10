import requests
import warnings

from brownie import Contract, accounts, chain
from brownie.convert import to_address

warnings.filterwarnings("ignore")

# This script is used to prepare, simulate and broadcast an arbitrary ownership vote
# (where the transaction is executed via 0x40907540d8a6c65c637785e8f8b742ae6b0b9968).

# address to create the vote from - you will need to modify this prior to mainnet use
SENDER = accounts.at("0x9B44473E223f8a3c047AD86f387B80402536B029", force=True)

# a list of calls to perform in the vote, formatted as a lsit of tuples
# in the format (target, function name, *input args).
#
# for example, to call:
# `GaugeController("0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB").add_gauge("0xFA712EE4788C042e2B7BB55E6cb8ec569C4530c1", 0, 0)
#
# use the following:
# [("0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB", "add_gauge", "0xFA712EE4788C042e2B7BB55E6cb8ec569C4530c1", 0, 0),]

ACTIONS = [
    # ("target", "fn_name", *args),
]

# metadata description to include with vote
# ipfs content should be in the form `{"text":"a description of the vote"}`
# you can use https://ipfsbrowser.com/ to pin the description file to IPFS
DESCRIPTION = "ipfs:[IPFS HASH HERE]"


def prepare_evm_script():
    agent = Contract("0x40907540d8a6c65c637785e8f8b742ae6b0b9968")
    evm_script = "0x00000001"

    for address, fn_name, *args in ACTIONS:
        contract = Contract(address)
        fn = getattr(contract, fn_name)
        calldata = fn.encode_input(*args)
        agent_calldata = agent.execute.encode_input(address, 0, calldata)[2:]
        length = hex(len(agent_calldata)//2)[2:].zfill(8)
        evm_script = f"{evm_script}{agent.address[2:]}{length}{agent_calldata}"

    print(f"EVM script: {evm_script}")

    return evm_script


def make_vote(sender=SENDER):
    aragon = Contract("0xe478de485ad2fe566d49342cbd03e49ed7db3356")

    evm_script = prepare_evm_script()
    tx = aragon.newVote(evm_script, DESCRIPTION, False, False, {'from': sender})
    vote_id = tx.events['StartVote']['voteId']

    return vote_id


def simulate():
    voting_escrow = Contract("0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2")
    aragon = Contract("0xe478de485ad2fe566d49342cbd03e49ed7db3356")

    # make the new vote
    vote_id = make_vote()

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

    # vote
    for acct in holders:
        aragon.vote(vote_id, True, False, {'from': acct})

    # sleep for a week so it has time to pass
    chain.sleep(86400*7)

    # moment of truth - execute the vote!
    aragon.executeVote(vote_id, {'from': holders[0]})
