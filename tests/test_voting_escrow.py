import brownie

DAY = 86400
WEEK = 7 * DAY
MAXTIME = 126144000


def test_escrow_desposit_withdraw(rpc, accounts, token, voting_escrow, block_timestamp):
    alice = accounts[0]
    from_alice = {'from': alice}

    alice_amount = 1000 * 10 ** 18
    alice_unlock_time = (block_timestamp() + 2 * WEEK) // WEEK * WEEK
    token.approve(voting_escrow.address, alice_amount * 10, from_alice)

    # Simple deposit / withdraw
    voting_escrow.deposit(alice_amount, alice_unlock_time, from_alice)
    with brownie.reverts():
        voting_escrow.withdraw(alice_amount, from_alice)
    rpc.sleep(2 * WEEK)
    rpc.mine()
    voting_escrow.withdraw(alice_amount, from_alice)
    with brownie.reverts():
        voting_escrow.withdraw(1, from_alice)

    # Deposit, add more, withdraw all
    alice_unlock_time = (block_timestamp() + 2 * WEEK) // WEEK * WEEK
    voting_escrow.deposit(alice_amount, alice_unlock_time, from_alice)
    rpc.sleep(WEEK)
    rpc.mine()
    with brownie.reverts():
        voting_escrow.deposit(alice_amount, alice_unlock_time - 1, from_alice)
    voting_escrow.deposit(alice_amount, from_alice)
    rpc.sleep(WEEK)
    rpc.mine()
    voting_escrow.withdraw(2 * alice_amount, from_alice)


def test_voting_powers(web3, rpc, accounts, block_timestamp,
                       token, voting_escrow):
    """
    Test voting power in the following scenario.
    Alice:
    ~~~~~~~
    ^
    | *       *
    | | \     |  \
    | |  \    |    \
    +-+---+---+------+---> t

    Bob:
    ~~~~~~~
    ^
    |         *
    |         | \
    |         |  \
    +-+---+---+---+--+---> t

    Alice has 100% of voting power in the first period.
    She has 2/3 power at the start of 2nd period, with Bob having 1/2 power
    (due to smaller locktime).
    Alice's power grows to 100% by Bob's unlock.

    Checking that totalSupply is appropriate.

    After the test is done, check all over again with balanceOfAt / totalSupplyAt
    """
    alice, bob = accounts[:2]
    amount = 1000 * 10 ** 18
    token.transfer(bob, amount, {'from': alice})
    stages = {}

    # Move to timing which is good for testing - beginning of a UTC week
    rpc.sleep((block_timestamp() // WEEK + 1) * WEEK)
    rpc.mine()

    token.approve(voting_escrow.address, amount * 10, {'from': alice})
    token.approve(voting_escrow.address, amount * 10, {'from': bob})

    assert voting_escrow.totalSupply() == 0
    assert voting_escrow.balanceOf(alice) == 0
    assert voting_escrow.balanceOf(bob) == 0

    stages['before_deposits'] = (web3.eth.blockNumber, block_timestamp())
    rpc.sleep(DAY)
    rpc.mine()

    stages['alice_deposit'] = []
    voting_escrow.deposit(amount, block_timestamp() + WEEK, {'from': alice})
    stages['alice_deposit'].append((web3.eth.blockNumber, block_timestamp()))

    assert voting_escrow.balanceOf(alice) == amount * WEEK // MAXTIME
    assert voting_escrow.balanceOf(bob) == 0
    assert voting_escrow.totalSupply() == amount * WEEK // MAXTIME

    for i in range(7):
        rpc.sleep(DAY)
        rpc.mine()
        stages['alice_deposit'].append((web3.eth.blockNumber, block_timestamp()))
    voting_escrow.withdraw(amount, {'from': alice})
    stages['alice_deposit'].append((web3.eth.blockNumber, block_timestamp()))

    rpc.sleep(DAY)
    rpc.mine()

    stages['both_deposit'] = []
    voting_escrow.deposit(amount, block_timestamp() + 2 * WEEK, {'from': alice})
    stages['both_deposit'].append((web3.eth.blockNumber, block_timestamp()))
    voting_escrow.deposit(amount, block_timestamp() + WEEK, {'from': bob})
    stages['both_deposit'].append((web3.eth.blockNumber, block_timestamp()))
    for i in range(7):
        rpc.sleep(DAY)
        rpc.mine()
        stages['both_deposit'].append((web3.eth.blockNumber, block_timestamp()))
    voting_escrow.withdraw(amount // 2, {'from': bob})
    stages['both_deposit'].append((web3.eth.blockNumber, block_timestamp()))
    for i in range(7):
        rpc.sleep(DAY)
        rpc.mine()
        stages['both_deposit'].append((web3.eth.blockNumber, block_timestamp()))
    voting_escrow.withdraw(amount, {'from': alice})
    stages['both_deposit'].append((web3.eth.blockNumber, block_timestamp()))
    voting_escrow.withdraw(amount - amount // 2, {'from': bob})
    stages['both_deposit'].append((web3.eth.blockNumber, block_timestamp()))

    rpc.sleep(DAY)
    rpc.mine()
