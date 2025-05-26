import pytest


DAY = 86400
WEEK = 7 * DAY


def test_deposited_after(web3, chain, accounts, voting_escrow, fee_distributor, coin_a, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18
    fee_distributor = fee_distributor()

    token.approve(voting_escrow.address, amount * 10, {"from": alice})
    coin_a._mint_for_testing(bob, 100 * 10 ** 18)

    for i in range(5):
        for j in range(7):
            coin_a.transfer(fee_distributor, 10 ** 18, {"from": bob})
            fee_distributor.checkpoint_token()
            fee_distributor.checkpoint_total_supply()
            chain.sleep(DAY)
            chain.mine()

    chain.sleep(WEEK)
    chain.mine()

    voting_escrow.create_lock(amount, chain[-1].timestamp + 3 * WEEK, {"from": alice})
    chain.sleep(2 * WEEK)

    fee_distributor.claim({"from": alice})

    assert coin_a.balanceOf(alice) == 0


def test_deposited_during(web3, chain, accounts, voting_escrow, fee_distributor, coin_a, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})
    coin_a._mint_for_testing(bob, 100 * 10 ** 18)

    chain.sleep(WEEK)
    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": alice})
    chain.sleep(WEEK)
    fee_distributor = fee_distributor()

    for i in range(3):
        for j in range(7):
            coin_a.transfer(fee_distributor, 10 ** 18, {"from": bob})
            fee_distributor.checkpoint_token()
            fee_distributor.checkpoint_total_supply()
            chain.sleep(DAY)
            chain.mine()

    chain.sleep(WEEK)
    fee_distributor.checkpoint_token()

    fee_distributor.claim({"from": alice})

    assert abs(coin_a.balanceOf(alice) - 21 * 10 ** 18) < 10


def test_deposited_before(web3, chain, accounts, voting_escrow, fee_distributor, coin_a, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})
    coin_a._mint_for_testing(bob, 100 * 10 ** 18)

    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": alice})
    chain.sleep(WEEK)
    chain.mine()
    start_time = int(chain.time())
    chain.sleep(WEEK * 5)

    fee_distributor = fee_distributor(t=start_time)
    coin_a.transfer(fee_distributor, 10 ** 19, {"from": bob})
    fee_distributor.checkpoint_token()
    chain.sleep(WEEK)
    fee_distributor.checkpoint_token()

    fee_distributor.claim({"from": alice})

    assert abs(coin_a.balanceOf(alice) - 10 ** 19) < 10


def test_deposited_twice(web3, chain, accounts, voting_escrow, fee_distributor, coin_a, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})
    coin_a._mint_for_testing(bob, 100 * 10 ** 18)

    voting_escrow.create_lock(amount, chain[-1].timestamp + 4 * WEEK, {"from": alice})
    chain.sleep(WEEK)
    chain.mine()
    start_time = int(chain.time())
    chain.sleep(WEEK * 3)
    voting_escrow.withdraw({"from": alice})
    exclude_time = chain[-1].timestamp // WEEK * WEEK  # Alice had 0 here
    voting_escrow.create_lock(amount, chain[-1].timestamp + 4 * WEEK, {"from": alice})
    chain.sleep(WEEK * 2)

    fee_distributor = fee_distributor(t=start_time)
    coin_a.transfer(fee_distributor, 10 ** 19, {"from": bob})
    fee_distributor.checkpoint_token()
    chain.sleep(WEEK)
    fee_distributor.checkpoint_token()

    fee_distributor.claim({"from": alice})

    tokens_to_exclude = fee_distributor.tokens_per_week(exclude_time)
    assert abs(10 ** 19 - coin_a.balanceOf(alice) - tokens_to_exclude) < 10


def test_deposited_parallel(web3, chain, accounts, voting_escrow, fee_distributor, coin_a, token):
    alice, bob, charlie = accounts[0:3]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})
    token.approve(voting_escrow.address, amount * 10, {"from": bob})
    token.transfer(bob, amount, {"from": alice})
    coin_a._mint_for_testing(charlie, 100 * 10 ** 18)

    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": alice})
    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": bob})
    chain.sleep(WEEK)
    chain.mine()
    start_time = int(chain.time())
    chain.sleep(WEEK * 5)

    fee_distributor = fee_distributor(t=start_time)
    coin_a.transfer(fee_distributor, 10 ** 19, {"from": charlie})
    fee_distributor.checkpoint_token()
    chain.sleep(WEEK)
    fee_distributor.checkpoint_token()

    fee_distributor.claim({"from": alice})
    fee_distributor.claim({"from": bob})

    balance_alice = coin_a.balanceOf(alice)
    balance_bob = coin_a.balanceOf(bob)
    assert balance_alice == balance_bob
    assert abs(balance_alice + balance_bob - 10 ** 19) < 20


def test_checkpoint_and_lock(CheckpointLock, accounts, chain, fee_distributor, voting_escrow, token, coin_a):
    distributor = fee_distributor()
    distributor.toggle_allow_checkpoint_token()
    contract = CheckpointLock.deploy(distributor, voting_escrow, token, {"from": accounts[0]})
    voting_escrow.commit_smart_wallet_checker(contract, {"from": voting_escrow.admin()})
    voting_escrow.apply_smart_wallet_checker({"from": voting_escrow.admin()})

    amount0, amount1 = 10 ** 18, 10 ** 18
    token.approve(contract, amount0 + amount1, {"from": accounts[0]})

    rounded_ts = (chain.time() + WEEK - 1) // WEEK * WEEK
    chain.mine(timestamp=rounded_ts - 1)
    contract.checkpoint_and_lock(amount0, amount1, {"from": accounts[0]})
    distributor.checkpoint_token()

    coin_a._mint_for_testing(distributor, 10 ** 18, {"from": accounts[0]})
    chain.mine(timestamp=rounded_ts + WEEK)

    amount = distributor.claim(contract, {"from": accounts[0]}).return_value
    assert int(amount) == pytest.approx(10 ** 18, rel=1e-5)
