def test_vested_supply(chain, vesting_simple, end_time):
    assert vesting_simple.vestedSupply() == 0
    chain.sleep(end_time - chain.time())
    chain.mine()
    assert vesting_simple.vestedSupply() == 10**20


def test_locked_supply(chain, vesting_simple, end_time):
    assert vesting_simple.lockedSupply() == 10**20
    chain.sleep(end_time - chain.time())
    chain.mine()
    assert vesting_simple.lockedSupply() == 0


def test_vested_of(chain, vesting_simple, accounts, end_time):
    assert vesting_simple.vestedOf(accounts[1]) == 0
    chain.sleep(end_time - chain.time())
    chain.mine()
    assert vesting_simple.vestedOf(accounts[1]) == 10**20


def test_locked_of(chain, vesting_simple, accounts, end_time):
    assert vesting_simple.lockedOf(accounts[1]) == 10**20
    chain.sleep(end_time - chain.time())
    chain.mine()
    assert vesting_simple.lockedOf(accounts[1]) == 0


def test_balance_of(chain, vesting_simple, accounts, end_time):
    assert vesting_simple.balanceOf(accounts[1]) == 0
    chain.sleep(end_time - chain.time())
    chain.mine()
    assert vesting_simple.balanceOf(accounts[1]) == 10**20
    vesting_simple.claim({'from': accounts[1]})
    assert vesting_simple.balanceOf(accounts[1]) == 0
