from brownie import Contract
from hexbytes import HexBytes
import warnings

warnings.filterwarnings("ignore")

# this script is used to decode an ownership vote - one originating
# from 0xe478de485ad2fe566d49342cbd03e49ed7db3356

# the vote ID you wish to decrypt
VOTE_ID = 29


def main(vote_id=VOTE_ID):
    aragon = Contract("0xe478de485ad2fe566d49342cbd03e49ed7db3356")

    script = HexBytes(aragon.getVote(vote_id)['script'])

    idx = 4
    while idx < len(script):
        target = Contract(script[idx:idx+20])
        idx += 20
        length = int(script[idx:idx+4].hex(), 16)
        idx += 4
        calldata = script[idx:idx+length]
        idx += length
        fn, inputs = target.decode_input(calldata)
        if calldata[:4].hex() == "0xb61d27f6":
            agent_target = Contract(inputs[0])
            fn, inputs = agent_target.decode_input(inputs[2])
            print(f"Call via agent ({target}):\n ├─ To: {agent_target}\n ├─ Function: {fn}\n └─ Inputs: {inputs}\n")
        else:
            print(f"Direct call:\n ├─ To: {target}\n ├─ Function: {fn}\n └─ Inputs: {inputs}")
