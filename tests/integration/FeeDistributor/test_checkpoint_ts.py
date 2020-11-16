import pytest
from brownie.test import given, strategy


WEEK = 86400 * 7


@pytest.fixture(scope="module")
def distributor(accounts, chain, fee_distributor, voting_escrow, token):
    distributor = fee_distributor()

    for i in range(10):
        token.approve(voting_escrow, 2**256-1, {'from': accounts[i]})
        token.transfer(accounts[i], 10**21, {'from': accounts[0]})

    yield distributor


@given(
    st_amount=strategy("decimal[10]", min_value=1, max_value=100, places=4, unique=True),
    st_locktime=strategy("uint256[10]", min_value=1, max_value=52, unique=True),
    st_sleep=strategy("uint256[10]", min_value=1, max_value=30, unique=True),
)
def test_checkpoint_total_supply(accounts, chain, distributor, voting_escrow, st_amount, st_locktime, st_sleep):
    final_lock = 0
    for i in range(10):
        chain.sleep(st_sleep[i] * 86400)
        lock_time = chain.time() + WEEK * st_locktime[i]
        final_lock = max(final_lock, lock_time)
        voting_escrow.create_lock(int(st_amount[i] * 10**18), lock_time, {'from': accounts[i]})

    while chain.time() < final_lock:

        week_epoch = (chain.time() + WEEK) // WEEK * WEEK
        chain.mine(timestamp=week_epoch)
        week_block = chain[-1].number
        chain.sleep(1)

        # Max: 42 weeks
        # doing checkpoint 3 times is enough
        for i in range(3):
            distributor.checkpoint_total_supply({'from': accounts[0]})

        assert distributor.ve_supply(week_epoch) == voting_escrow.totalSupplyAt(week_block)
