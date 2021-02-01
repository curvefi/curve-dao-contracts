import requests
from brownie import web3

import numpy as np
import pylab

START_BLOCK = 10647813 + 86400
graph_url = "https://api.thegraph.com/subgraphs/name/pengiundev/curve-votingescrow3"
query = {
    "query": """query ($block: Int!, $first: Int!, $skip: Int!) {\n  userBalances(orderBy: weight, orderDirection: desc, first: $first, skip: $skip, block: {number: $block}) {\n    id\n    startTx\n    user\n    CRVLocked\n lock_start\n    unlock_time\n    weight\n    __typename\n  }\n}\n""",  # noqa
    "variables": {"block": None, "first": 1000, "skip": 0},
}


def gini(x):
    # from https://stackoverflow.com/questions/39512260/calculating-gini-coefficient-in-python-numpy
    # (Warning: This is a concise implementation, but it is O(n**2)
    # in time and memory, where n = len(x).  *Don't* pass in huge
    # samples!)

    # Mean absolute difference
    mad = np.abs(np.subtract.outer(x, x)).mean()
    # Relative mean absolute difference
    rmad = mad / np.mean(x)
    # Gini coefficient
    g = 0.5 * rmad
    return g


def main():
    current_block = web3.eth.blockNumber
    blocks = np.linspace(START_BLOCK, current_block, 50)
    ginis = []
    for block in blocks:
        query["variables"]["block"] = int(block)
        while True:
            try:
                resp = requests.post(graph_url, json=query).json()
                weights = [int(u["weight"]) / 1e18 for u in resp["data"]["userBalances"]]
            except KeyError:
                print("Error")
                continue
            break
        ginis.append(gini(weights))
        print(block, ginis[-1])

    pylab.plot(blocks, ginis)
    pylab.title("Gini coefficient")
    pylab.xlabel("Block number")
    pylab.ylabel("veCRV Gini coefficient")
    pylab.show()
