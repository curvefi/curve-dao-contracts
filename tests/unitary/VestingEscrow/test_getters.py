import pytest

amounts = [10**17 * i for i in range(1, 11)]


@pytest.fixture(scope="module", autouse=True)
def initial_funding(vesting, accounts):
    vesting.fund(accounts[:10], amounts, {'from': accounts[0]})


def test_vested_supply(chain, vesting, accounts, end_time):
    assert vesting.vestedSupply() == 0
    chain.sleep(end_time - chain.time())
    chain.mine()
    assert vesting.vestedSupply() == sum(amounts)
