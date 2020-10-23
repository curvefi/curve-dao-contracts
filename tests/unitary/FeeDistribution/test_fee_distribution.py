DAY = 86400
WEEK = 7 * DAY


def test_deposited_after(web3, chain, accounts, voting_escrow, fee_distributor, coin_a, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18
    fee_distributor = fee_distributor()

    token.approve(voting_escrow.address, amount * 10, {'from': alice})
    coin_a._mint_for_testing(100 * 10 ** 18, {'from': bob})

    for i in range(5):
        for j in range(7):
            coin_a.transfer(fee_distributor, 10**18, {'from': bob})
            fee_distributor.checkpoint_token()
            fee_distributor.checkpoint_total_supply()
            chain.sleep(DAY)
            chain.mine()

    chain.sleep(WEEK)
    chain.mine()

    voting_escrow.create_lock(amount, chain[-1].timestamp + 3*WEEK, {'from': alice})
    chain.sleep(2*WEEK)

    fee_distributor.claim({'from': alice})

    assert coin_a.balanceOf(alice) == 0


def test_deposited_during(web3, chain, accounts, voting_escrow, fee_distributor, coin_a, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {'from': alice})
    coin_a._mint_for_testing(100 * 10 ** 18, {'from': bob})

    chain.sleep(WEEK)
    voting_escrow.create_lock(amount, chain[-1].timestamp + 8*WEEK, {'from': alice})  # 5
    chain.sleep(WEEK)
    fee_distributor = fee_distributor()

    # XXX to fix - these should not be needed
    fee_distributor.checkpoint_token()
    fee_distributor.checkpoint_total_supply()
    # XXX

    for i in range(3):
        for j in range(7):
            coin_a.transfer(fee_distributor, 10**18, {'from': bob})
            fee_distributor.checkpoint_token()
            fee_distributor.checkpoint_total_supply()
            chain.sleep(DAY)
            chain.mine()

    chain.sleep(WEEK)
    chain.mine()

    fee_distributor.claim({'from': alice})

    assert abs(coin_a.balanceOf(alice) - 21 * 10**18) < 10
