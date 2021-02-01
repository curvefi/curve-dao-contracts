import warnings

import requests
from brownie import Contract, accounts, chain
from brownie.convert import to_address

warnings.filterwarnings("ignore")

# this script is used to prepare, simulate and broadcast votes within Curve's DAO
# modify the constants below according the the comments, and then use `simulate` in
# a forked mainnet to verify the result of the vote prior to broadcasting on mainnet

# addresses related to the DAO - these should not need modifications
CURVE_DAO = {
    "agent": "0x40907540d8a6c65c637785e8f8b742ae6b0b9968",
    "voting": "0xe478de485ad2fe566d49342cbd03e49ed7db3356",
    "token": "0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2",
    "quorum": 30,
}


EMERGENCY_DAO = {
    "forwarder": "0xf409Ce40B5bb1e4Ef8e97b1979629859c6d5481f",
    "agent": "0x00669DF67E4827FCc0E48A1838a8d5AB79281909",
    "voting": "0x1115c9b3168563354137cdc60efb66552dd50678",
    "token": "0x4c0947B16FB1f755A2D32EC21A0c4181f711C500",
    "quorum": 51,
}

# the intended target of the vote, should be one of the above constant dicts
TARGET = CURVE_DAO

# address to create the vote from - you will need to modify this prior to mainnet use
SENDER = accounts.at("0x9B44473E223f8a3c047AD86f387B80402536B029", force=True)

# a list of calls to perform in the vote, formatted as a lsit of tuples
# in the format (target, function name, *input args).
#
# for example, to call:
# `GaugeController("0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB").add_gauge("0xFA712...", 0, 0)
#
# use the following:
# [("0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB", "add_gauge", "0xFA712...", 0, 0),]

ACTIONS = [
    # ("target", "fn_name", *args),
]

# metadata description to include with vote
# ipfs content should be in the form `{"text":"a description of the vote"}`
# you can use https://ipfsbrowser.com/ to pin the description file to IPFS
DESCRIPTION = "ipfs:[IPFS HASH HERE]"


def prepare_evm_script():
    agent = Contract(TARGET["agent"])
    evm_script = "0x00000001"

    for address, fn_name, *args in ACTIONS:
        contract = Contract(address)
        fn = getattr(contract, fn_name)
        calldata = fn.encode_input(*args)
        agent_calldata = agent.execute.encode_input(address, 0, calldata)[2:]
        length = hex(len(agent_calldata) // 2)[2:].zfill(8)
        evm_script = f"{evm_script}{agent.address[2:]}{length}{agent_calldata}"

    return evm_script


def make_vote(sender=SENDER):
    aragon = Contract(TARGET["voting"])

    evm_script = prepare_evm_script()
    if TARGET.get("forwarder"):
        # the emergency DAO only allows new votes via a forwarder contract
        # so we have to wrap the call in another layer of evm script
        vote_calldata = aragon.newVote.encode_input(evm_script, DESCRIPTION, False, False)[2:]
        length = hex(len(vote_calldata) // 2)[2:].zfill(8)
        evm_script = f"0x00000001{aragon.address[2:]}{length}{vote_calldata}"
        print(f"Target: {TARGET['forwarder']}\nEVM script: {evm_script}")
        tx = Contract(TARGET["forwarder"]).forward(evm_script, {"from": sender})
    else:
        print(f"Target: {aragon.address}\nEVM script: {evm_script}")
        tx = aragon.newVote(evm_script, DESCRIPTION, False, False, {"from": sender})

    vote_id = tx.events["StartVote"]["voteId"]

    return vote_id


def simulate():
    # fetch the top holders so we can pass the vote
    data = requests.get(
        f"https://api.ethplorer.io/getTopTokenHolders/{TARGET['token']}",
        params={"apiKey": "freekey", "limit": 50},
    ).json()["holders"][::-1]

    # create a list of top holders that will be sufficient to make quorum
    holders = []
    weight = 0
    while weight < TARGET["quorum"] + 5:
        row = data.pop()
        holders.append(to_address(row["address"]))
        weight += row["share"]

    # make the new vote
    top_holder = holders[0]
    vote_id = make_vote(top_holder)

    # vote
    aragon = Contract(TARGET["voting"])
    for acct in holders:
        aragon.vote(vote_id, True, False, {"from": acct})

    # sleep for a week so it has time to pass
    chain.sleep(86400 * 7)

    # moment of truth - execute the vote!
    aragon.executeVote(vote_id, {"from": top_holder})
