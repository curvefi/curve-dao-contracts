from random import randrange
from .conftest import YEAR


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
