import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_balanceOf(vesting, coin_a, accounts):
    amounts = [10**17 * i for i in range(1, 11)]
    vesting.fund(accounts[:10], amounts, {'from': accounts[0]})

    assert coin_a.balanceOf(vesting) == sum(amounts)
    assert coin_a.balanceOf(accounts[0]) == 10**21 - sum(amounts)


def test_initial_locked_supply(vesting, accounts):
    amounts = [10**17 * i for i in range(1, 11)]
    vesting.fund(accounts[:10], amounts, {'from': accounts[0]})

    assert vesting.initial_locked_supply() == sum(amounts)


def test_initial_locked(vesting, accounts):
    amounts = [10**17 * i for i in range(1, 11)]
    vesting.fund(accounts[:10], amounts, {'from': accounts[0]})

    for acct, expected_amount in zip(accounts, amounts):
        assert vesting.initial_locked(acct) == expected_amount


def test_event(vesting, accounts):
    amounts = [10**17 * i for i in range(1, 11)]
    tx = vesting.fund(accounts[:10], amounts, {'from': accounts[0]})

    assert len(tx.events['Fund']) == 10
    for event, acct, expected_amount in zip(tx.events['Fund'], accounts, amounts):
        assert event.values() == [acct, expected_amount]


def test_partial_recipients(vesting, accounts):
    amounts = [10**17 * i for i in range(1, 11)]
    vesting.fund(accounts[:5]+[ZERO_ADDRESS]*5, amounts, {'from': accounts[0]})

    assert vesting.initial_locked_supply() == sum(amounts[:5])


def test_one_recipient(vesting, accounts):
    recipients = [accounts[5]] + [ZERO_ADDRESS] * 9
    vesting.fund(recipients, [10**20]+[0]*9, {'from': accounts[0]})

    assert vesting.initial_locked_supply() == 10**20


def test_multiple_calls_different_recipients(vesting, accounts):
    recipients = [accounts[5]] + [ZERO_ADDRESS] * 9
    amounts = [10**20, 10**20 * 2] + [0]*8
    vesting.fund(recipients, amounts, {'from': accounts[0]})

    recipients[:2] = [accounts[4], accounts[6]]
    vesting.fund(recipients, amounts, {'from': accounts[0]})

    assert vesting.initial_locked_supply() == 10**20 * 4
    assert vesting.initial_locked(accounts[4]) == 10**20
    assert vesting.initial_locked(accounts[5]) == 10**20
    assert vesting.initial_locked(accounts[6]) == 10**20 * 2


def test_multiple_calls_same_recipient(vesting, accounts):
    recipients = [accounts[5]] + [ZERO_ADDRESS] * 9
    amounts = [10**20 * 2] + [0] * 9
    vesting.fund(recipients, amounts, {'from': accounts[0]})

    amounts[0] = 10**20
    vesting.fund(recipients, amounts, {'from': accounts[0]})

    assert vesting.initial_locked_supply() == 10**20 * 3
    assert vesting.initial_locked(accounts[5]) == 10**20 * 3


def test_admin_only(vesting, accounts):
    with brownie.reverts("dev: admin only"):
        vesting.fund(accounts[:10], [10**18] * 10, {'from': accounts[1]})


def test_transfer_fails(vesting, accounts):
    with brownie.reverts("dev: transfer failed"):
        vesting.fund(accounts[:10], [10**21] * 10, {'from': accounts[0]})
