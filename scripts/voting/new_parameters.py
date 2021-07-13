from datetime import datetime

from brownie import Contract, chain

import scripts.voting.new_vote as vote

# This script updates parameters of pools via 'new_vote.py'
# Update all lines marked 'CHANGE'

POOL_PROXY = "0xeCb456EA5365865EbAb8a2661B0c503410e9B347"
FACTORY_PROXY = "0x8CF8Af108B3B46DDC6AD596aebb917E053F0D72b"
REGISTRY = "0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5"

ADMIN_ACTIONS_DELAY = 3 * 86400

new_parameters = [  # CHANGE
    # ("new_fee", pool: address, new_fee: int, new_admin_fee: int)
    # ("ramp_A", pool: address, is_factory_pool: bool, new_A: int, future_time: int)
    # ("new_parameters", pool: address, new_A: int, new_fee: int, new_admin_fee: int,
    # min_asymmetry: int)
]
# Fetch contracts
new_parameters = [(params[0], Contract(params[1]), *params[2:]) for params in new_parameters]
logs = [[] for _ in range(len(new_parameters))]


def main():
    for i, params in enumerate(new_parameters):
        if params[0] == "new_fee":
            add_new_fee(i, *params[1:])
        elif params[0] == "ramp_A":
            add_ramp_A(i, *params[1:])
        elif params[0] == "new_parameters":
            add_new_parameters(i, *params[1:])
        else:
            raise ValueError(f"Unknown action: {params}")

    vote.TARGET = vote.CURVE_DAO_PARAM
    vote.DESCRIPTION = ""  # CHANGE
    if False:  # CHANGE for prod
        vote.make_vote(vote.SENDER)  # CHANGE
        return
    vote.simulate()

    # Check every pool separately
    check_new_fee()
    check_ramp_A()
    check_new_parameters()

    check_all_params()
    # Finally all set


def add_new_fee(i: int, pool: Contract, new_fee: int, new_admin_fee: int):
    vote.ACTIONS.append(
        (POOL_PROXY, "commit_new_fee", pool.address, new_fee, new_admin_fee),
    )
    logs[i].extend(
        [
            f"Address: {pool.address}",
            f"Pool: {Contract(REGISTRY).get_pool_name(pool)}",
            f"Current fee: {pool.fee()}",
            f"Current admin_fee: {pool.admin_fee()}",
            "",
        ]
    )


def check_new_fee():
    for i, params in enumerate(new_parameters):
        if params[0] == "new_fee":
            chain.snapshot()
            _, pool, new_fee, new_admin_fee = params

            chain.sleep(ADMIN_ACTIONS_DELAY)
            Contract(POOL_PROXY).apply_new_fee(params[1], {"from": vote.SENDER})

            fee = pool.fee()
            admin_fee = pool.admin_fee()

            ts = chain.time()
            logs[i].extend(
                [
                    datetime.fromtimestamp(ts).ctime() + f", ts: {ts}",
                    f"New fee: {fee}",
                    f"New admin_fee: {admin_fee}",
                    "",
                ]
            )
            print(*logs[i], "", sep="\n")

            assert fee == new_fee
            assert admin_fee == new_admin_fee

            chain.revert()


def add_ramp_A(i: int, pool: Contract, is_factory_pool: bool, new_A: int, future_time: int):
    vote.ACTIONS.append(
        (
            FACTORY_PROXY if is_factory_pool else POOL_PROXY,
            "ramp_A",
            pool.address,
            new_A,
            future_time,
        ),
    )
    logs[i].extend(
        [
            f"Address: {pool.address}",
            f"Pool: {pool.name() if is_factory_pool else Contract(REGISTRY).get_pool_name(pool)}",
            f"Current A: {pool.A()}",
            f"Current initial_A: {getattr(pool, 'initial_A', lambda: None)()}",
            f"Current future_A: {pool.future_A()}",
            f"Ramping to {new_A} by {future_time}",
            "",
        ]
    )


def check_ramp_A():
    for i, params in enumerate(new_parameters):
        if params[0] == "ramp_A":
            chain.snapshot()
            _, pool, is_factory_pool, new_A, future_time = params

            initial_time = pool.initial_A_time()
            checks_num = 4
            for c in range(checks_num + 1):
                ts = ((checks_num - c) * initial_time + c * future_time) // checks_num
                chain.mine(1, timestamp=ts)
                logs[i].append(f"{datetime.fromtimestamp(ts).ctime()}, ts: {ts}, A: {pool.A()}")

            print(*logs[i], "", "", sep="\n")
            assert pool.A() == new_A
            assert pool.future_A_time() == future_time

            # Does not change after
            chain.mine(1, 2 * future_time)
            assert pool.A() == new_A

            chain.revert()


def add_new_parameters(
    i: int, pool: Contract, new_A: int, new_fee: int, new_admin_fee: int, min_asymmetry: int
):
    vote.ACTIONS.append(
        (
            POOL_PROXY,
            "commit_new_parameters",
            pool.address,
            new_A,
            new_fee,
            new_admin_fee,
            min_asymmetry,
        ),
    )
    logs[i].extend(
        [
            f"Address: {pool.address}",
            f"Pool: {Contract(REGISTRY).get_pool_name(pool)}",
            f"Current A: {pool.A()}",
            f"Current fee: {pool.fee()}",
            f"Current admin_fee: {pool.admin_fee()}",
            "",
        ]
    )


def check_new_parameters():
    for i, params in enumerate(new_parameters):
        if params[0] == "new_parameters":
            chain.snapshot()
            _, pool, new_A, new_fee, new_admin_fee, min_asymmetry = params

            chain.sleep(ADMIN_ACTIONS_DELAY)
            assert Contract(POOL_PROXY).min_asymmetries(pool) == min_asymmetry
            Contract(POOL_PROXY).apply_new_parameters(pool, {"from": vote.SENDER})

            A = pool.A()
            fee = pool.fee()
            admin_fee = pool.admin_fee()

            ts = chain.time()
            logs[i].extend(
                [
                    datetime.fromtimestamp(ts).ctime() + f", ts: {ts}",
                    f"New A: {A}",
                    f"New fee: {fee}",
                    f"New admin_fee: {admin_fee}",
                    "",
                ]
            )
            print(*logs[i], "", sep="\n")

            assert A == new_A
            assert fee == new_fee
            assert admin_fee == new_admin_fee

            chain.revert()


def check_all_params():
    """ Extra check, that eventually all parameters are correct. """
    chain.sleep(ADMIN_ACTIONS_DELAY)
    for params in new_parameters:
        if params[0] == "new_fee":
            Contract(POOL_PROXY).apply_new_fee(params[1], {"from": vote.SENDER})
        elif params[0] == "new_parameters":
            Contract(POOL_PROXY).apply_new_parameters(params[1], {"from": vote.SENDER})

    chain.mine(1, timestamp=chain.time() + 365 * 86400)
    for params in new_parameters:
        if params[0] == "new_fee":
            _, pool, new_fee, new_admin_fee = params
            assert pool.fee() == new_fee
            assert pool.admin_fee() == new_admin_fee
        elif params[0] == "ramp_A":
            _, pool, _, new_A, _ = params
            assert pool.A() == new_A
        elif params[0] == "new_parameters":
            _, pool, new_A, new_fee, new_admin_fee, _ = params
            pool: Contract
            assert pool.A() == new_A
            assert pool.fee() == new_fee
            assert pool.admin_fee() == new_admin_fee
