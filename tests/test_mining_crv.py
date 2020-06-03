import brownie
from brownie.test import strategy, given

from random import random, randrange
from math import log10
from .conftest import approx
from .conftest import YEAR, YEAR_1_SUPPLY


def test_update_mining_parameters(token, rpc, accounts):
    creation_time = token.start_epoch_time()
    new_epoch = creation_time + YEAR - rpc.time()
    rpc.sleep(new_epoch)
    token.update_mining_parameters({'from': accounts[0]})


def test_update_mining_parameters_same_epoch(token, rpc, accounts):
    creation_time = token.start_epoch_time()
    new_epoch = creation_time + YEAR - rpc.time()
    rpc.sleep(new_epoch - 3)
    with brownie.reverts("dev: too soon!"):
        token.update_mining_parameters({'from': accounts[0]})


@given(time=strategy("decimal", min_value=1, max_value=7))
def test_mintable_in_timeframe(accounts, token, block_timestamp, theoretical_supply, time, rpc):
    t0 = token.start_epoch_time()
    rpc.sleep(int(10 ** time))
    rpc.mine()
    t1 = block_timestamp()
    if t1 - t0 >= YEAR:
        token.update_mining_parameters({'from': accounts[0]})

    t1 = block_timestamp()
    available_supply = token.available_supply()
    mintable = token.mintable_in_timeframe(t0, t1)
    assert (available_supply - (10 ** 9 * 10 ** 18)) >= mintable  # Should only round down, not up
    if t1 == t0:
        assert mintable == 0
    else:
        assert (available_supply - (10 ** 9 * 10 ** 18)) / mintable - 1 < 1e-7
    assert approx(theoretical_supply(), available_supply, 1e-16)


@given(time1=strategy('uint', max_value=YEAR), time2=strategy('uint', max_value=YEAR))
def test_random_range_year_one(token, block_timestamp, rpc, accounts, time1, time2):
    creation_time = token.start_epoch_time()
    start, end = sorted((creation_time+time1, creation_time+time2))
    rate = YEAR_1_SUPPLY // YEAR

    assert token.mintable_in_timeframe(start, end) ==  rate * (end-start)


@given(start=strategy('uint', max_value=YEAR*6), duration=strategy('uint', max_value=YEAR))
def test_random_range_multiple_epochs(token, block_timestamp, rpc, accounts, start, duration):
    creation_time = token.start_epoch_time()
    start += creation_time
    end = duration + start
    start_epoch = (start - creation_time) // YEAR
    end_epoch = (end - creation_time) // YEAR
    rate = int(YEAR_1_SUPPLY // YEAR / (2 ** 0.5) ** start_epoch)

    for i in range(end_epoch):
        rpc.sleep(YEAR)
        rpc.mine()
        token.update_mining_parameters({'from': accounts[0]})

    if start_epoch == end_epoch:
        assert approx(token.mintable_in_timeframe(start, end), rate * (end-start), 1e-16)
    else:
        assert token.mintable_in_timeframe(start, end) < rate * end


# TODO
def test_mint(ERC20CRV, accounts, rpc, block_timestamp):
    token = ERC20CRV.deploy("Curve DAO Token", "CRV", 18, 10 ** 9, {'from': accounts[0]})

    owner, bob = accounts[:2]

    # Sometimes can go across epochs
    for i in range(20):
        to_mint = token.available_supply() - token.totalSupply()
        assert to_mint >= 0
        t0 = block_timestamp()
        if to_mint > 0:
            token.mint(owner, to_mint, {'from': owner})
        # All minted before t0 (including t0)
        # Blocks move by 1 s here, so cannot mint rate + 1
        rate = token.rate()
        with brownie.reverts():
            # Sometimes rate decreases in this block - that tx will fail too
            if to_mint == 0:
                token.mint(owner, rate + 1, {'from': owner})
            else:
                # We had a new transaction which didn't mint an extra rate amount
                token.mint(owner, 2 * rate + 1, {'from': owner})
        rpc.sleep(1)
        rpc.mine()
        t0 = block_timestamp()  # Next tx will be in future block which is at least 1 s away

        rpc.sleep(int(10 ** (random() * log10(300 * 86400))))
        rpc.mine()
        t1 = block_timestamp()
        balance_before = token.balanceOf(bob)

        t_start = randrange(t0, t1 + 1)

        if t1 > t_start:
            dt = int(10 ** (random() * log10(t1 - t_start)))
        else:
            dt = 0
        with brownie.reverts():
            # -2 for two previous mints (failed and nonfailed), -1 for next block,
            # +1 for t0 (it was in the same block as the last mint) and -1 more into the past
            non_mintable_value = token.mintable_in_timeframe(t0 - 3, t1)
            token.mint(bob, non_mintable_value, {'from': owner})
        value = token.mintable_in_timeframe(t_start, t_start + dt)
        value = min(value, int(value * random() * 2))
        token.mint(bob, value, {'from': owner})

        balance_after = token.balanceOf(bob)
        assert balance_after - balance_before == value

        t0 = t1
