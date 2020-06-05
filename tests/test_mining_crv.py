import brownie
from brownie.test import strategy, given

from random import random, randrange
from math import log10
from .conftest import approx
from .conftest import YEAR, YEAR_1_SUPPLY


WEEK = 86400 * 7

def test_start_epoch_time_write(token, rpc, accounts):
    creation_time = token.start_epoch_time()
    rpc.sleep(YEAR)
    rpc.mine()

    # the constant function should not report a changed value
    assert token.start_epoch_time() == creation_time

    # the state-changing function should show the changed value
    assert token.start_epoch_time_write().return_value == creation_time + YEAR

    # after calling the state-changing function, the view function is changed
    assert token.start_epoch_time() == creation_time + YEAR


def test_start_epoch_time_write_same_epoch(token, rpc, accounts):
    # calling `start_epoch_token_write` within the same epoch should not raise
    token.start_epoch_time_write()
    token.start_epoch_time_write()


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


def test_mintable_in_timeframe_end_before_start(token, accounts):
    creation_time = token.start_epoch_time()
    with brownie.reverts("dev: start > end"):
        token.mintable_in_timeframe(creation_time + 1, creation_time)


def test_mintable_in_timeframe_multiple_epochs(token, accounts):
    creation_time = token.start_epoch_time()

    # two epochs should not raise
    token.mintable_in_timeframe(creation_time, int(creation_time + YEAR * 1.9))

    with brownie.reverts("dev: too far in future"):
        # three epochs should raise
        token.mintable_in_timeframe(creation_time, int(creation_time + YEAR * 2.1))


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


@given(duration=strategy('uint', min_value=1, max_value=YEAR))
def test_available_supply(rpc, web3, token, duration):
    creation_time = token.start_epoch_time()
    initial_supply = token.totalSupply()
    rate = token.rate()
    rpc.sleep(duration)
    rpc.mine()

    expected = initial_supply + (web3.eth.getBlock('latest')['timestamp'] - creation_time) * rate
    assert token.available_supply() == expected


@given(duration=strategy('uint', min_value=1, max_value=YEAR))
def test_mint(accounts, rpc, token, duration):
    creation_time = token.start_epoch_time()
    initial_supply = token.totalSupply()
    rate = token.rate()
    rpc.sleep(duration)

    amount = (rpc.time()-creation_time) * rate
    token.mint(accounts[1], amount, {'from': accounts[0]})

    assert token.balanceOf(accounts[1]) == amount
    assert token.totalSupply() == initial_supply + amount


@given(duration=strategy('uint', min_value=1, max_value=YEAR))
def test_overmint(accounts, rpc, token, duration):
    creation_time = token.start_epoch_time()
    rate = token.rate()
    rpc.sleep(duration)

    with brownie.reverts("dev: exceeds allowable mint amount"):
        token.mint(accounts[1], (rpc.time()-creation_time+2) * rate, {'from': accounts[0]})


@given(durations=strategy('uint[5]', min_value=YEAR*0.33, max_value=YEAR*0.9))
def test_mint_multiple(accounts, rpc, token, durations):
    total_supply = token.totalSupply()
    balance = 0
    epoch_start = token.start_epoch_time()

    for time in durations:
        rpc.sleep(time)

        if rpc.time() - epoch_start > YEAR:
            token.update_mining_parameters({'from': accounts[0]})
            epoch_start = token.start_epoch_time()

        amount = token.available_supply() - total_supply
        token.mint(accounts[1], amount, {'from': accounts[0]})

        balance += amount
        total_supply += amount

        assert token.balanceOf(accounts[1]) == balance
        assert token.totalSupply() == total_supply
