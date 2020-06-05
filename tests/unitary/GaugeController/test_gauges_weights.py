import pytest

WEEK = 7 * 86400
YEAR = 365 * 86400

TYPE_WEIGHTS = [5 * 10 ** 17, 2 * 10 ** 18]
GAUGE_WEIGHTS = [2 * 10 ** 18, 10 ** 18, 5 * 10 ** 17]


def test_add_gauges(accounts, gauge_controller, three_gauges):
    gauge_controller.add_gauge(three_gauges[0], 0, {'from': accounts[0]})
    gauge_controller.add_gauge(three_gauges[1], 0, {'from': accounts[0]})

    assert gauge_controller.gauges(0) == three_gauges[0]
    assert gauge_controller.gauges(1) == three_gauges[1]


def test_n_gauges(accounts, gauge_controller, three_gauges):
    assert gauge_controller.n_gauges() == 0

    gauge_controller.add_gauge(three_gauges[0], 0, {'from': accounts[0]})
    gauge_controller.add_gauge(three_gauges[1], 0, {'from': accounts[0]})

    assert gauge_controller.n_gauges() == 2


@pytest.mark.xfail(reason="Adding a gauge twice overwrites the data but the count still increments")
def test_n_gauges_same_gauge(accounts, gauge_controller, three_gauges):

    assert gauge_controller.n_gauges() == 0
    gauge_controller.add_gauge(three_gauges[0], 0, {'from': accounts[0]})
    gauge_controller.add_gauge(three_gauges[1], 0, {'from': accounts[0]})

    assert gauge_controller.n_gauges() == 1


def test_n_gauge_types(gauge_controller, accounts, three_gauges):
    assert gauge_controller.n_gauge_types() == 1

    gauge_controller.add_type(b'Insurance', {'from': accounts[0]})

    assert gauge_controller.n_gauge_types() == 2


def test_gauge_types(accounts, gauge_controller, three_gauges):
    gauge_controller.add_type(b'Insurance', {'from': accounts[0]})
    gauge_controller.add_gauge(three_gauges[0], 1, {'from': accounts[0]})
    gauge_controller.add_gauge(three_gauges[1], 0, {'from': accounts[0]})

    assert gauge_controller.gauge_types(three_gauges[0]) == 1
    assert gauge_controller.gauge_types(three_gauges[1]) == 0


def test_gauge_weight(accounts, gauge_controller, gauge):
    gauge_controller.add_gauge(gauge, 0, 10**19, {'from': accounts[0]})

    assert gauge_controller.get_gauge_weight.call(gauge) == 10**19


def test_gauge_weight_as_zero(accounts, gauge_controller, gauge):
    gauge_controller.add_gauge(gauge, 0, {'from': accounts[0]})

    assert gauge_controller.get_gauge_weight.call(gauge) == 0


def test_set_gauge_weight(accounts, gauge_controller, gauge):
    gauge_controller.add_gauge(gauge, 0, {'from': accounts[0]})
    gauge_controller.change_gauge_weight(gauge, 10**21)

    assert gauge_controller.get_gauge_weight.call(gauge) == 10**21


def test_type_weight(accounts, gauge_controller):
    gauge_controller.add_type(b'Insurance', {'from': accounts[0]})

    assert gauge_controller.get_type_weight.call(0) == TYPE_WEIGHTS[0]
    assert gauge_controller.get_type_weight.call(1) == 0


def test_change_type_weight(accounts, gauge_controller):
    gauge_controller.add_type(b'Insurance', {'from': accounts[0]})

    gauge_controller.change_type_weight(1, TYPE_WEIGHTS[1], {'from': accounts[0]})
    gauge_controller.change_type_weight(0, 31337, {'from': accounts[0]})

    assert gauge_controller.get_type_weight.call(0) == 31337
    assert gauge_controller.get_type_weight.call(1) == TYPE_WEIGHTS[1]


def test_relative_weight_write(accounts, rpc, gauge_controller, three_gauges):
    gauge_controller.add_type(b'Insurance', TYPE_WEIGHTS[1], {'from': accounts[0]})
    gauge_controller.add_gauge(three_gauges[0], 0, GAUGE_WEIGHTS[0], {'from': accounts[0]})
    gauge_controller.add_gauge(three_gauges[1], 0, GAUGE_WEIGHTS[1], {'from': accounts[0]})
    gauge_controller.add_gauge(three_gauges[2], 1, GAUGE_WEIGHTS[2], {'from': accounts[0]})

    rpc.sleep(int(1.1 * YEAR))
    gauge_controller.period_write({'from': accounts[0]})

    # Fill weights and check that nothing has changed
    period = gauge_controller.period()
    for gauge in three_gauges:
        weight = gauge_controller.gauge_relative_weight(gauge, period)
        gauge_controller.gauge_relative_weight_write(gauge, period, {'from': accounts[0]})
        assert gauge_controller.gauge_relative_weight(gauge, period) == weight


def test_gauge_weight_vote(accounts, rpc, block_timestamp, gauge_controller, three_gauges, voting_escrow, token):
    admin, bob, charlie = accounts[0:3]
    gauge_controller.add_type(b'Liquidity', {'from': admin})  # 0
    gauge_controller.change_type_weight(0, 10 ** 18, {'from': admin})

    # Set up gauges and types
    gauge_controller.add_gauge(three_gauges[0].address, 0, {'from': admin})
    gauge_controller.add_gauge(three_gauges[1].address, 0, {'from': admin})
    gauge_controller.add_gauge(three_gauges[2].address, 0, {'from': admin})
    # gauge_controller.add_gauge(three_gauges[2].address, 0, 10 ** 18, {'from': admin})

    # Distribute coins
    token.transfer(bob, 10 ** 6 * 10 ** 18, {'from': admin})
    token.approve(voting_escrow, 5 * 10 ** 5 * 10 ** 18, {'from': admin})
    token.approve(voting_escrow, 10 ** 6 * 10 ** 18, {'from': bob})

    # Deposit for voting
    t = block_timestamp()
    # Same voting power initially, but as Bob unlocks, his power drops
    voting_escrow.deposit(5 * 10 ** 5 * 10 ** 18, t + 2 * YEAR, {'from': admin})
    voting_escrow.deposit(10 ** 6 * 10 ** 18, t + YEAR, {'from': bob})

    # Users vote. Initially total weights are equal, though will only be enacted in a week
    gauge_controller.vote_for_gauge_weights(0, 6000, {'from': admin})
    gauge_controller.vote_for_gauge_weights(1, 3000, {'from': admin})
    gauge_controller.vote_for_gauge_weights(1, 3000, {'from': bob})
    gauge_controller.vote_for_gauge_weights(2, 6000, {'from': bob})

    assert gauge_controller.vote_user_power(admin) == gauge_controller.vote_user_power(bob) == 9000

    admin_initial_bias = voting_escrow.get_last_user_slope(admin) * (voting_escrow.locked__end(admin) - t)
    admin_lock_duration = (t + 2 * YEAR) // WEEK * WEEK - t
    bob_initial_bias = voting_escrow.get_last_user_slope(bob) * (voting_escrow.locked__end(bob) - t)
    bob_lock_duration = (t + YEAR) // WEEK * WEEK - t
    bob_lock_fraction = bob_lock_duration / admin_lock_duration
    admin_model = lambda x: max(admin_initial_bias * (1 - x), 0)
    bob_model = lambda x: max(bob_initial_bias * (1 - x / bob_lock_fraction), 0)

    while True:
        for j in range(3):
            gauge_controller.enact_vote(j, {'from': charlie})

        relative_time = (block_timestamp() - t) / admin_lock_duration
        weights = [gauge_controller.gauge_relative_weight(three_gauges[j].address) / 1e18 for j in range(3)]
        theoretical_weights = [
            0.6 * admin_model(relative_time),
            0.3 * (admin_model(relative_time) + bob_model(relative_time)),
            0.6 * bob_model(relative_time)
        ]
        theoretical_weights = [w and (w / sum(theoretical_weights)) for w in theoretical_weights]
        if block_timestamp() >= (t + WEEK) // WEEK * WEEK:
            for j in range(3):
                assert abs(weights[j] - theoretical_weights[j]) <= WEEK / YEAR

        if block_timestamp() - t > 2 * 365 * 86400:
            break
        dt = randrange(1, 30 * 86400)
        rpc.sleep(dt)
        rpc.mine()
