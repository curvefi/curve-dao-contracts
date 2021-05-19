import json
from pathlib import Path

from brownie import Contract, FeeDistributor, accounts, chain


def main():
    alice = accounts[0]
    fee_token = Contract("0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490")
    voting_escrow = Contract("0x5f3b5dfeb7b28cdbd7faba78963ee202a494e2a2")

    # sept 17, 2020 - 2 days before admin fee collection begins
    start_time = 1600300800
    distributor = FeeDistributor.deploy(
        voting_escrow, start_time, fee_token, alice, alice, {"from": alice}
    )

    # transfer 2m USD of 3CRV
    fee_token.mint(
        distributor, 2000000 * 10 ** 18, {"from": "0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7"},
    )

    distributor.checkpoint_token()
    distributor.checkpoint_total_supply()
    chain.sleep(86400 * 14)
    distributor.checkpoint_token()
    distributor.checkpoint_total_supply()

    with Path("votelocks-11237343.json").open() as fp:
        data = json.load(fp)
    data = set([i["provider"] for i in data])

    for c, acct in enumerate(data):
        print(f"Claiming, {c}/{len(data)}")

        # ensure we claim up to the user's max epoch, some accounts require multiple claims
        max_epoch = voting_escrow.user_point_epoch(acct)
        epoch = 0

        while epoch < max_epoch:
            distributor.claim({"from": acct})
            epoch = distributor.user_epoch_of(acct)

    amount = fee_token.balanceOf(distributor)
    print(f"Remaining fee balance: ${amount/1e18:,.2f}")
