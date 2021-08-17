import itertools

import brownie
import pytest

TYPE_WEIGHTS = [5e17, 1e19]
GAUGE_WEIGHTS = [1e19, 1e18, 5e17]
GAUGE_TYPES = [0, 0, 1]

MONTH = 86400 * 30
WEEK = 7 * 86400


@pytest.fixture(scope="module", autouse=True)
def distributor_setup(accounts, mock_lp_token, gauge_controller, three_gauges, chain):
    # ensure the tests all begin at the start of the epoch week
    chain.mine(timestamp=(chain.time() / WEEK + 1) * WEEK)

    # set types
    for weight in TYPE_WEIGHTS:
        gauge_controller.add_type(b"Liquidity", weight, {"from": accounts[0]})

    # add gauges
    for i in range(3):
        gauge_controller.add_gauge(
            three_gauges[i], GAUGE_TYPES[i], GAUGE_WEIGHTS[i], {"from": accounts[0]}
        )

    # transfer tokens
    for acct in accounts[1:4]:
        mock_lp_token.transfer(acct, 1e18, {"from": accounts[0]})

    # approve gauges
    for gauge, acct in itertools.product(three_gauges, accounts[1:4]):
        mock_lp_token.approve(gauge, 1e18, {"from": acct})


def test_distribute(accounts, chain, three_gauges, distributor, token):
    three_gauges[0].deposit(1e18, {"from": accounts[1]})

    chain.sleep(MONTH)
    distributor.distribute(three_gauges[0], {"from": accounts[1]})
    expected = three_gauges[0].integrate_fraction(accounts[1])

    assert expected > 0
    assert token.balanceOf(accounts[1]) == expected
    assert distributor.distributed(accounts[1], three_gauges[0]) == expected


def test_distribute_immediate(accounts, chain, three_gauges, distributor, token):
    three_gauges[0].deposit(1e18, {"from": accounts[1]})
    t0 = chain.time()
    chain.sleep((t0 + WEEK) // WEEK * WEEK - t0 + 1)  # 1 second more than enacting the weights

    distributor.distribute(three_gauges[0], {"from": accounts[1]})
    balance = token.balanceOf(accounts[1])

    assert balance > 0
    assert distributor.distributed(accounts[1], three_gauges[0]) == balance


def test_distribute_multiple_same_gauge(accounts, chain, three_gauges, distributor, token):
    three_gauges[0].deposit(1e18, {"from": accounts[1]})

    chain.sleep(MONTH)
    distributor.distribute(three_gauges[0], {"from": accounts[1]})
    balance = token.balanceOf(accounts[1])

    chain.sleep(MONTH)
    distributor.distribute(three_gauges[0], {"from": accounts[1]})
    expected = three_gauges[0].integrate_fraction(accounts[1])
    final_balance = token.balanceOf(accounts[1])

    assert final_balance > balance
    assert final_balance == expected
    assert distributor.distributed(accounts[1], three_gauges[0]) == expected


def tes_distribute_multiple_gauges(accounts, chain, three_gauges, distributor, token):
    for i in range(3):
        three_gauges[i].deposit((i + 1) * 10 ** 17, {"from": accounts[1]})

    chain.sleep(MONTH)

    for i in range(3):
        distributor.distribute(three_gauges[i], {"from": accounts[1]})

    total_dist = 0
    for i in range(3):
        gauge = three_gauges[i]
        distributed = distributor.distributed(accounts[1], gauge)
        assert distributed == gauge.integrate_fraction(accounts[1])
        total_dist += distributed

    assert token.balanceOf(accounts[1]) == total_dist


def test_distribute_after_withdraw(accounts, chain, three_gauges, distributor, token):
    three_gauges[0].deposit(1e18, {"from": accounts[1]})

    chain.sleep(2 * WEEK)
    three_gauges[0].withdraw(1e18, {"from": accounts[1]})
    distributor.distribute(three_gauges[0], {"from": accounts[1]})

    assert token.balanceOf(accounts[1]) > 0


def test_distribute_multiple_after_withdraw(accounts, chain, three_gauges, distributor, token):
    three_gauges[0].deposit(1e18, {"from": accounts[1]})

    chain.sleep(10)
    three_gauges[0].withdraw(1e18, {"from": accounts[1]})
    distributor.distribute(three_gauges[0], {"from": accounts[1]})
    balance = token.balanceOf(accounts[1])

    chain.sleep(10)
    distributor.distribute(three_gauges[0], {"from": accounts[1]})

    # shouldn't have distributed any new tokens to accounts[1]
    assert token.balanceOf(accounts[1]) == balance


def test_no_deposit(accounts, chain, three_gauges, distributor, token):
    distributor.distribute(three_gauges[0], {"from": accounts[1]})

    assert token.balanceOf(accounts[1]) == 0
    assert distributor.distributed(accounts[1], three_gauges[0]) == 0


def test_distribute_wrong_gauge(accounts, chain, three_gauges, distributor, token):
    three_gauges[0].deposit(1e18, {"from": accounts[1]})

    chain.sleep(MONTH)
    distributor.distribute(three_gauges[1], {"from": accounts[1]})

    assert token.balanceOf(accounts[1]) == 0
    assert distributor.distributed(accounts[1], three_gauges[0]) == 0
    assert distributor.distributed(accounts[1], three_gauges[1]) == 0


def test_distribute_not_a_gauge(accounts, distributor):
    with brownie.reverts("dev: gauge is not added"):
        distributor.distribute(accounts[1], {"from": accounts[0]})


def test_distribute_before_inflation_begins(accounts, chain, three_gauges, distributor, token):
    three_gauges[0].deposit(1e18, {"from": accounts[1]})

    chain.sleep(distributor.start_epoch_time() - chain.time() - 5)
    distributor.distribute(three_gauges[0], {"from": accounts[1]})

    assert token.balanceOf(accounts[1]) == 0
    assert distributor.distributed(accounts[1], three_gauges[0]) == 0
