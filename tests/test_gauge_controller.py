from random import randrange
from .conftest import YEAR

WEEK = 7 * 86400


def test_gauge_controller(accounts, rpc, block_timestamp, gauge_controller, three_gauges):
    admin = accounts[0]
    type_weights = [5 * 10 ** 17, 2 * 10 ** 18]
    gauge_weights = [2 * 10 ** 18, 10 ** 18, 5 * 10 ** 17]

    # Set up gauges and types
    gauge_controller.add_type(b'Liquidity', {'from': admin})  # 0
    gauge_controller.add_type(b'Insurance', {'from': admin})  # 1
    gauge_controller.change_type_weight(0, type_weights[0], {'from': admin})

    gauge_controller.add_gauge(three_gauges[0].address, 0, {'from': admin})
    rpc.sleep(randrange(3))
    gauge_controller.add_gauge(three_gauges[1].address, 0, gauge_weights[1], {'from': admin})
    rpc.sleep(randrange(3))
    gauge_controller.add_gauge(three_gauges[2].address, 1, gauge_weights[2], {'from': admin})
    rpc.sleep(randrange(3))

    gauge_controller.change_type_weight(1, type_weights[1], {'from': admin})
    rpc.sleep(randrange(3))

    gauge_controller.change_gauge_weight(
        three_gauges[0].address, gauge_weights[0], {'from': admin}
    )
    rpc.sleep(randrange(3))

    last_change = block_timestamp()
    assert last_change == gauge_controller.last_change.call()

    # Check static parameters
    assert gauge_controller.n_gauge_types() == 2
    assert gauge_controller.n_gauges() == 3
    for i in range(3):
        assert three_gauges[i].address == gauge_controller.gauges(i)
    assert gauge_controller.gauge_types(three_gauges[0].address) == 0
    assert gauge_controller.gauge_types(three_gauges[1].address) == 0
    assert gauge_controller.gauge_types(three_gauges[2].address) == 1
    for i in range(3):
        assert gauge_controller.get_gauge_weight.call(three_gauges[i].address) == gauge_weights[i]
    for i in range(2):
        assert gauge_controller.get_type_weight.call(i) == type_weights[i]

    # Check incremental calculations
    sums = [sum(gauge_weights[:2]), gauge_weights[2]]
    assert gauge_controller.get_weights_sum_per_type.call(0) == sums[0]
    assert gauge_controller.get_weights_sum_per_type.call(1) == sums[1]
    total_weight = sum(s * t for s, t in zip(sums, type_weights))
    assert gauge_controller.get_total_weight.call() == total_weight
    for i, t in [(0, 0), (1, 0), (2, 1)]:
        assert gauge_controller.gauge_relative_weight(three_gauges[i].address) ==\
            10 ** 18 * type_weights[t] * gauge_weights[i] // total_weight

    # Change epoch using the time machine
    before = gauge_controller.period()
    rpc.sleep(int(1.1 * YEAR))
    rpc.mine()
    gauge_controller.period_write({'from': admin})
    after = gauge_controller.period()
    assert after == before + 1

    # Check that no timestamps are missed and everything is incremental
    prev_ts = 0
    for i in range(gauge_controller.period()):
        ts = gauge_controller.period_timestamp(i)
        assert ts > 0
        assert ts >= prev_ts
        prev_ts = ts

    # Fill weights and check that nothing has changed
    p = gauge_controller.period()
    for i in range(3):
        w1 = gauge_controller.gauge_relative_weight(three_gauges[i].address, p)
        gauge_controller.gauge_relative_weight_write(three_gauges[i].address, p, {'from': admin})
        w2 = gauge_controller.gauge_relative_weight(three_gauges[i].address, p)
        assert w1 == w2


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
