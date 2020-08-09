import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
AMOUNTS = [10**17 * i for i in range(1, 101)]


@pytest.fixture(scope="module", autouse=True)
def initial_setup(accounts, vesting):
    vesting.add_tokens(10**21, {'from': accounts[0]})


def test_balanceOf(coin_a, vesting):
    assert coin_a.balanceOf(vesting) == 10**21


def test_initial_locked_supply(vesting, accounts):
    vesting.fund(accounts[:100], AMOUNTS, {'from': accounts[0]})

    assert vesting.initial_locked_supply() == sum(AMOUNTS)


def test_unallocated_supply(vesting, accounts):
    vesting.fund(accounts[:100], AMOUNTS, {'from': accounts[0]})

    assert vesting.unallocated_supply() == 10**21 - sum(AMOUNTS)


def test_initial_locked(vesting, accounts):
    vesting.fund(accounts[:100], AMOUNTS, {'from': accounts[0]})

    for acct, expected_amount in zip(accounts, AMOUNTS):
        assert vesting.initial_locked(acct) == expected_amount


def test_event(vesting, accounts):
    tx = vesting.fund(accounts[:100], AMOUNTS, {'from': accounts[0]})

    assert len(tx.events['Fund']) == 100
    for event, acct, expected_amount in zip(tx.events['Fund'], accounts, AMOUNTS):
        assert event.values() == [acct, expected_amount]


def test_partial_recipients(vesting, accounts):
    recipients = accounts[:5] + [ZERO_ADDRESS] * (len(AMOUNTS) - 5)
    vesting.fund(recipients, AMOUNTS, {'from': accounts[0]})

    assert vesting.initial_locked_supply() == sum(AMOUNTS[:5])


def test_one_recipient(vesting, accounts):
    recipients = [accounts[5]] + [ZERO_ADDRESS] * 99
    vesting.fund(recipients, [10**20]+[0]*99, {'from': accounts[0]})

    assert vesting.initial_locked_supply() == 10**20


def test_multiple_calls_different_recipients(vesting, accounts):
    recipients = [accounts[5]] + [ZERO_ADDRESS] * 99
    amounts = [10**20, 10**20 * 2] + [0]*98
    vesting.fund(recipients, amounts, {'from': accounts[0]})

    recipients[:2] = [accounts[4], accounts[6]]
    vesting.fund(recipients, amounts, {'from': accounts[0]})

    assert vesting.initial_locked_supply() == 10**20 * 4
    assert vesting.unallocated_supply() == 10**21 - (10**20 * 4)
    assert vesting.initial_locked(accounts[4]) == 10**20
    assert vesting.initial_locked(accounts[5]) == 10**20
    assert vesting.initial_locked(accounts[6]) == 10**20 * 2


def test_multiple_calls_same_recipient(vesting, accounts):
    recipients = [accounts[5]] + [ZERO_ADDRESS] * 99
    amounts = [10**20 * 2] + [0] * 99
    vesting.fund(recipients, amounts, {'from': accounts[0]})

    amounts[0] = 10**20
    vesting.fund(recipients, amounts, {'from': accounts[0]})

    assert vesting.initial_locked_supply() == 10**20 * 3
    assert vesting.unallocated_supply() == 10**21 - (10**20 * 3)
    assert vesting.initial_locked(accounts[5]) == 10**20 * 3


def test_admin_only(vesting, accounts):
    with brownie.reverts("dev: admin only"):
        vesting.fund(accounts[:100], [10**18] * 100, {'from': accounts[6]})


def test_over_allocation(vesting, accounts):
    with brownie.reverts("Integer underflow"):
        vesting.fund(accounts[:100], [10**21 + 1] + [0] * 99, {'from': accounts[0]})


@pytest.mark.parametrize("idx", range(1, 5))
def test_fund_admin(vesting, accounts, idx):
    recipients = [accounts[5]] + [ZERO_ADDRESS] * 99
    amounts = [10**20, 10**20 * 2] + [0]*98
    vesting.fund(recipients, amounts, {'from': accounts[idx]})

    assert vesting.initial_locked_supply() == 10**20
    assert vesting.unallocated_supply() == 10**21 - 10**20
    assert vesting.initial_locked(accounts[5]) == 10**20


@pytest.mark.parametrize("idx", range(1, 5))
def test_disabled_fund_admin(vesting, accounts, idx):
    vesting.disable_fund_admins({'from': accounts[0]})

    recipients = [accounts[5]] + [ZERO_ADDRESS] * 99
    amounts = [10**20, 10**20 * 2] + [0]*98
    with brownie.reverts("dev: fund admins disabled"):
        vesting.fund(recipients, amounts, {'from': accounts[idx]})
