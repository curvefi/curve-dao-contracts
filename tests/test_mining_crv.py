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
        t0 = randrange(creation_time, now)
        dt = int(10 ** (random() * log10(now - t0)))
        start_epoch = (t0 - creation_time) // YEAR
        end_epoch = (t0 + dt - creation_time) // YEAR
        rate = int(YEAR_1_SUPPLY // YEAR / (2 ** 0.5) ** start_epoch)

        if start_epoch == end_epoch:
            assert approx(token.caller.mintable_in_timeframe(t0, t0 + dt), rate * dt, 1e-16)
        else:
            assert token.caller.mintable_in_timeframe(t0, t0 + dt) < rate * dt


def test_mint(w3, token):
    owner = w3.eth.accounts[0]
    from_owner = {'from': owner}
    bob = w3.eth.accounts[1]
    t0 = block_timestamp(w3)

    # Sometimes can go across epochs
    for i in range(20):
        to_mint = token.caller.available_supply() - token.caller.totalSupply()
        assert to_mint >= 0
        t0 = block_timestamp(w3)
        if to_mint > 0:
            token.functions.mint(owner, to_mint).transact(from_owner)
        # All minted before t0 (including t0)
        # Blocks move by 1 s here, so cannot mint rate + 1
        rate = token.caller.rate()
        with pytest.raises(TransactionFailed):
            # Sometimes rate decreases in this block - that tx will fail too
            if to_mint == 0:
                token.functions.mint(owner, rate + 1).transact(from_owner)
            else:
                # We had a new transaction which didn't mint an extra rate amount
                token.functions.mint(owner, 2 * rate + 1).transact(from_owner)
        t0 = block_timestamp(w3)  # Next tx will be in future block which is at least 1 s away

        t1 = time_travel(w3, int(10 ** (random() * log10(300 * 86400))))
        balance_before = token.caller.balanceOf(bob)

        t_start = randrange(t0, t1 + 1)

        if t1 > t_start:
            dt = int(10 ** (random() * log10(t1 - t_start)))
        else:
            dt = 0
        with pytest.raises(TransactionFailed):
            # -2 for two previous mints (failed and nonfailed), -1 for next block,
            # +1 for t0 (it was in the same block as the last mint) and -1 more into the past
            non_mintable_value = token.caller.mintable_in_timeframe(t0 - 3, t1)
            token.functions.mint(bob, non_mintable_value).transact(from_owner)
        value = token.caller.mintable_in_timeframe(t_start, t_start + dt)
        value = min(value, int(value * random() * 2))
        token.functions.mint(bob, value).transact(from_owner)

        balance_after = token.caller.balanceOf(bob)
        assert balance_after - balance_before == value

        t0 = t1
