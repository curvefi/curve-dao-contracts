import pytest
import math

WEEK = 7 * 86400


@pytest.fixture(autouse=True)
def local_setup(alice, chain, gauge_controller, liquidity_gauge, root_gauge, token, minter):
    token.set_minter(minter, {"from": alice})
    chain.mine(timedelta=WEEK)
    token.update_mining_parameters({"from": alice})

    gauge_controller.add_type("Test", 10 ** 18, {"from": alice})
    gauge_controller.add_gauge(liquidity_gauge, 0, 0, {"from": alice})
    gauge_controller.add_gauge(root_gauge, 0, 1, {"from": alice})

    chain.mine(timedelta=WEEK)


@pytest.mark.skip_coverage
def test_relative_weight_write(alice, chain, gauge_controller, liquidity_gauge, root_gauge, token):
    rate = token.rate()
    total_emissions = 0
    assert rate > 0

    for i in range(1, 110):
        # 110 weeks ensures we see 2 reductions in the rate
        root_gauge.checkpoint()
        new_emissions = root_gauge.emissions() - total_emissions
        expected = rate * WEEK // i

        assert math.isclose(new_emissions, expected)

        total_emissions += new_emissions
        rate = token.rate()

        # increaseing the gauge weight on `liquidity_gauge` each week reducees
        # the expected emission for `root_gauge` in the following week
        gauge_controller.change_gauge_weight(liquidity_gauge, i, {"from": alice})
        chain.mine(timedelta=WEEK)
