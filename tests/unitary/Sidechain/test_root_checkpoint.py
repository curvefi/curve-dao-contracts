import math

import pytest
from brownie import chain

WEEK = 7 * 86400
YEAR = 365 * 86400


@pytest.mark.skip_coverage
def test_emissions_against_expected(alice, gauge_controller, liquidity_gauge, root_gauge, token):
    gauge_controller.add_type("Test", 10 ** 18, {"from": alice})
    gauge_controller.add_gauge(liquidity_gauge, 0, 0, {"from": alice})
    gauge_controller.add_gauge(root_gauge, 0, 1, {"from": alice})

    chain.mine(timedelta=WEEK)

    rate = token.rate()
    total_emissions = 0
    assert rate > 0

    # we now have a one week delay in the emission of rewards, so new emissions from
    # the root gauge should equal the emissions of 1 week prior not 1 week ahead
    last_week_expected = 0
    # 110 weeks ensures we see 2 reductions in the rate
    for i in range(1, 110):

        this_week = chain[-1].timestamp // WEEK * WEEK
        last_week = this_week - WEEK
        start_epoch_time = root_gauge.start_epoch_time()
        future_epoch_time = start_epoch_time + YEAR
        gauge_weight = gauge_controller.gauge_relative_weight(root_gauge, last_week)

        # calculate the expected emissions, and checkpoint to update actual emissions
        if last_week <= future_epoch_time < this_week:
            # the core of the maff, q
            expected = gauge_weight * rate * (future_epoch_time - last_week) / 10 ** 18
            rate = rate * 10 ** 18 // 1189207115002721024
            expected += gauge_weight * rate * (this_week - future_epoch_time) / 10 ** 18
        else:
            expected = gauge_weight * rate * WEEK // 10 ** 18

        root_gauge.checkpoint()

        # actual emissions should equal expected emissions
        new_emissions = root_gauge.emissions() - total_emissions
        assert math.isclose(new_emissions, last_week_expected)

        total_emissions += new_emissions
        last_week_expected = expected

        # increasing the gauge weight on `liquidity_gauge` each week reducees
        # the expected emission for `root_gauge` in the following week
        gauge_controller.change_gauge_weight(liquidity_gauge, i, {"from": alice})
        chain.mine(timedelta=WEEK)

        # crossing over epochs our the rate should be the same as prior to the
        # epoch transition
        if this_week < future_epoch_time < this_week + WEEK:
            assert rate > token.rate()
        else:
            assert rate == token.rate()


@pytest.mark.skip_coverage
def test_emissions_against_other_gauge(
    alice, mock_lp_token, gauge_controller, liquidity_gauge, root_gauge
):
    gauge_controller.add_type("Test", 10 ** 18, {"from": alice})
    gauge_controller.add_gauge(liquidity_gauge, 0, 1, {"from": alice})
    gauge_controller.add_gauge(root_gauge, 0, 1, {"from": alice})

    # alice is the only staker in `liquidity_gauge`
    mock_lp_token.approve(liquidity_gauge, 2 ** 256 - 1, {"from": alice})
    tx = liquidity_gauge.deposit(100000, {"from": alice})

    # sleep until the start of the next epoch week
    chain.mine(timestamp=(tx.timestamp // WEEK + 1) * WEEK)

    # 110 weeks ensures we see 2 reductions in the rate
    for i in range(1, 110):
        # checkpointing the root gauge mints all the allocated emissions for the next week
        tx = root_gauge.checkpoint()
        emissions = root_gauge.emissions()  # emissions this week are delayed y a week so

        claimable = liquidity_gauge.claimable_tokens(alice, {"from": alice}).return_value

        # root gauge emissions should be equal to regular gauge claimable amount
        assert math.isclose(emissions, claimable, rel_tol=1e-6)

        # now we time travel one week, and get the claimable rewards from the regular gauge
        chain.mine(timestamp=(tx.timestamp // WEEK + 1) * WEEK)
