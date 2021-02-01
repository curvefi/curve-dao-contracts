import pytest

amounts = [10 ** 17 * i for i in range(1, 101)]


@pytest.fixture(scope="module", autouse=True)
def initial_funding(vesting, accounts):
    vesting.add_tokens(10 ** 21, {"from": accounts[0]})
    vesting.fund(accounts[:100], amounts, {"from": accounts[0]})


def test_vested_supply(chain, vesting, end_time):
    assert vesting.vestedSupply() == 0
    chain.sleep(end_time - chain.time())
    chain.mine()
    assert vesting.vestedSupply() == sum(amounts)


def test_locked_supply(chain, vesting, end_time):
    assert vesting.lockedSupply() == sum(amounts)
    chain.sleep(end_time - chain.time())
    chain.mine()
    assert vesting.lockedSupply() == 0


def test_vested_of(chain, vesting, accounts, end_time):
    assert vesting.vestedOf(accounts[0]) == 0
    chain.sleep(end_time - chain.time())
    chain.mine()
    assert vesting.vestedOf(accounts[0]) == amounts[0]


def test_locked_of(chain, vesting, accounts, end_time):
    assert vesting.lockedOf(accounts[0]) == amounts[0]
    chain.sleep(end_time - chain.time())
    chain.mine()
    assert vesting.lockedOf(accounts[0]) == 0


def test_balance_of(chain, vesting, accounts, end_time):
    assert vesting.balanceOf(accounts[0]) == 0
    chain.sleep(end_time - chain.time())
    chain.mine()
    assert vesting.balanceOf(accounts[0]) == amounts[0]
    vesting.claim({"from": accounts[0]})
    assert vesting.balanceOf(accounts[0]) == 0
