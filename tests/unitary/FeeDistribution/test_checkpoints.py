
WEEK = 86400 * 7

def test_checkpoint_total_supply(fee_distributor, chain,accounts, voting_escrow, token):
    fee_distributor = fee_distributor()
    start_time = fee_distributor.time_cursor()

    token.approve(voting_escrow, 2**256-1, {'from': accounts[0]})
    voting_escrow.create_lock(10**21, chain.time() + WEEK * 4, {'from': accounts[0]})

    chain.time() + WEEK // WEEK * WEEK

    next_week = ((chain.time() + WEEK) // WEEK * WEEK)
    chain.mine(timestamp=next_week)
    fee_distributor.checkpoint_total_supply({'from': accounts[0]})

    assert fee_distributor.ve_supply(start_time) == 0
    assert fee_distributor.ve_supply(start_time + WEEK) == voting_escrow.totalSupplyAt(chain[-2].number)

