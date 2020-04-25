import pytest
from eth_tester.exceptions import TransactionFailed
from random import random, randrange
from math import log10
from .conftest import time_travel, theoretical_supply, block_timestamp, approx
from .conftest import YEAR, YEAR_1_SUPPLY


def test_mintable_in_timeframe(w3, token):
    owner = w3.eth.accounts[0]
    from_owner = {'from': owner}
    creation_time = token.caller.start_epoch_time()

    # Sometimes can go across epochs
    for i in range(20):
        dt = int(10 ** (random() * log10(300 * 86400)))
        t0 = token.caller.start_epoch_time()
        t1 = time_travel(w3, dt)
        if t1 - t0 >= YEAR:
            token.functions.update_mining_parameters().transact(from_owner)
        else:
            with pytest.raises(TransactionFailed):
                token.functions.update_mining_parameters().transact(from_owner)

        available_supply = token.caller.available_supply()
        mintable = token.caller.mintable_in_timeframe(creation_time, t1)
        assert (available_supply - (10 ** 9 * 10 ** 18)) >= mintable  # Should only round down, not up
        assert (available_supply - (10 ** 9 * 10 ** 18)) / mintable - 1 < 1e-7
        assert approx(theoretical_supply(w3, token), available_supply, 1e-16)

    now = block_timestamp(w3)
    # Check random ranges
    for i in range(20):
        t0 = randrange(creation_time, now + 1)
        dt = int(10 ** (random() * log10(now - t0)))
        start_epoch = (t0 - creation_time) // YEAR
        end_epoch = (t0 + dt - creation_time) // YEAR
        rate = int(YEAR_1_SUPPLY // YEAR / (2 ** 0.5) ** start_epoch)

        if start_epoch == end_epoch:
            assert approx(token.caller.mintable_in_timeframe(t0, t0 + dt), rate * (dt + 1), 1e-16)
        else:
            assert token.caller.mintable_in_timeframe(t0, t0 + dt) < rate * (dt + 1)


def test_mints(w3, token):
    pass
