
YEAR = 365 * 86400


def test_advance_period(accounts, rpc, gauge_controller):
    before = gauge_controller.period()
    rpc.sleep(int(1.1 * YEAR))
    gauge_controller.period_write({'from': accounts[0]})

    assert gauge_controller.period() == before + 1


def test_period_timestamps(accounts, rpc, gauge_controller):
    for i in range(5):
        rpc.sleep(int(1.1 * YEAR))
        gauge_controller.period_write({'from': accounts[0]})

    # Check that no timestamps are missed and everything is incremental
    prev_ts = 0
    for i in range(gauge_controller.period()):
        ts = gauge_controller.period_timestamp(i)
        assert ts > 0
        assert ts >= prev_ts
        prev_ts = ts
