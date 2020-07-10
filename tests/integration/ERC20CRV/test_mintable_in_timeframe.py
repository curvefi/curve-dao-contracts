from brownie.test import strategy, given

from tests.conftest import approx
from tests.conftest import YEAR, YEAR_1_SUPPLY, INITIAL_SUPPLY


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
    assert (available_supply - (INITIAL_SUPPLY * 10 ** 18)) >= mintable  # Should only round down, not up
    if t1 == t0:
        assert mintable == 0
    else:
        assert (available_supply - (INITIAL_SUPPLY * 10 ** 18)) / mintable - 1 < 1e-7

    assert approx(theoretical_supply(), available_supply, 1e-16)


@given(time1=strategy('uint', max_value=YEAR), time2=strategy('uint', max_value=YEAR))
def test_random_range_year_one(token, block_timestamp, rpc, accounts, time1, time2):
    creation_time = token.start_epoch_time()
    start, end = sorted((creation_time+time1, creation_time+time2))
    rate = YEAR_1_SUPPLY // YEAR

    assert token.mintable_in_timeframe(start, end) == rate * (end-start)


@given(start=strategy('uint', max_value=YEAR*6), duration=strategy('uint', max_value=YEAR))
def test_random_range_multiple_epochs(token, block_timestamp, rpc, accounts, start, duration):
    creation_time = token.start_epoch_time()
    start += creation_time
    end = duration + start
    start_epoch = (start - creation_time) // YEAR
    end_epoch = (end - creation_time) // YEAR
    rate = int(YEAR_1_SUPPLY // YEAR / (2 ** 0.25) ** start_epoch)

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
