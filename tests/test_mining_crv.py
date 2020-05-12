import brownie

from random import random, randrange
from math import log10
from .conftest import approx
from .conftest import YEAR, YEAR_1_SUPPLY


def test_mintable_in_timeframe(
        web3, accounts, rpc, block_timestamp,
        theoretical_supply, token):
    owner = accounts[0]
    creation_time = token.start_epoch_time()

    # Sometimes can go across epochs
    for i in range(20):
        dt = int(10 ** (random() * log10(300 * 86400)))
        t0 = token.start_epoch_time()
        rpc.sleep(dt)
        rpc.mine()
        t1 = block_timestamp()
        if t1 - t0 >= YEAR:
            token.update_mining_parameters({'from': owner})
        else:
            with brownie.reverts():
                token.update_mining_parameters({'from': owner})
        t1 = block_timestamp()

        available_supply = token.available_supply()
        mintable = token.mintable_in_timeframe(creation_time, t1)
        assert (available_supply - (10 ** 9 * 10 ** 18)) >= mintable  # Should only round down, not up
        if t1 == t0:
            assert mintable == 0
        else:
            assert (available_supply - (10 ** 9 * 10 ** 18)) / mintable - 1 < 1e-7
        assert approx(theoretical_supply(), available_supply, 1e-16)

    now = block_timestamp()
    # Check random ranges
    for i in range(20):
        t0 = randrange(creation_time, now)
        dt = int(10 ** (random() * log10(now - t0)))
        start_epoch = (t0 - creation_time) // YEAR
        end_epoch = (t0 + dt - creation_time) // YEAR
        rate = int(YEAR_1_SUPPLY // YEAR / (2 ** 0.5) ** start_epoch)

        if start_epoch == end_epoch:
            assert approx(token.mintable_in_timeframe(t0, t0 + dt), rate * dt, 1e-16)
        else:
            assert token.mintable_in_timeframe(t0, t0 + dt) < rate * dt


def test_mint(web3, accounts, rpc, block_timestamp, token):
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
