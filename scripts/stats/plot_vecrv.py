from brownie import Contract, web3

import numpy as np
import pylab

START_BLOCK = 10647813


def main():
    vecrv = Contract("0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2")
    current_block = web3.eth.blockNumber
    blocks = np.linspace(START_BLOCK, current_block, 100)
    powers = [vecrv.totalSupplyAt(int(block)) / 1e18 for block in blocks]

    pylab.plot(blocks, powers)
    pylab.xlabel("Block number")
    pylab.ylabel("Total veCRV")
    pylab.show()
