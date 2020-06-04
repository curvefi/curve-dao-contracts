import pytest

from hypothesis import settings

from brownie import history, rpc
from brownie.test import given, strategy

WEEK = 86400 * 7
YEAR = 86400 * 365


@pytest.fixture(scope="module", autouse=True)
def setup(gauge_controller, accounts, three_gauges, token, voting_escrow):

    # Set up gauges and types
    gauge_controller.add_type(b'Liquidity', 10**18, {'from': accounts[0]})
    for gauge in three_gauges:
        gauge_controller.add_gauge(gauge, 0, {'from': accounts[0]})

    # Distribute coins
    for acct in accounts[:3]:
        token.transfer(acct, 10 ** 24, {'from': accounts[0]})
        token.approve(voting_escrow, 10 ** 24, {'from': acct})


@given(
    st_deposits = strategy('uint256[3]', min_value=10**21, max_value=10**23),
    st_length = strategy('uint256[3]', min_value=52, max_value=100),
    st_votes = strategy('uint[2][3]', min_value=1, max_value=5)
)
@settings(max_examples=10)
@pytest.mark.xfail(reason="Pls halp me Michael")
def test_gauge_weight_vote(accounts, gauge_controller, three_gauges, voting_escrow, st_deposits, st_length, st_votes):

    # Deposit for voting
    timestamp = history[-1].timestamp
    for i, acct in enumerate(accounts[:3]):
        voting_escrow.deposit(st_deposits[i], timestamp + (st_length[i] * WEEK), {'from': acct})

    # Place votes
    votes = []
    for i, acct in enumerate(accounts[:3]):
        votes.append([x*1000 for x in st_votes[i]])
        votes[-1].append(10000-sum(votes[-1]))
        for x in range(3):
            gauge_controller.vote_for_gauge_weights(x, votes[-1][x], {'from': acct})

    # Vote power assertions
    for acct in accounts[:3]:
        assert gauge_controller.vote_user_power(acct) == 10000

    # Calculate slope data, build model functions
    data = []
    for acct in accounts[:3]:
        initial_bias = voting_escrow.get_last_user_slope(acct) * (voting_escrow.locked__end(acct) - timestamp)
        duration = timestamp + (st_length[i] * WEEK) // WEEK * WEEK - timestamp
        data.append((initial_bias, duration))

    max_duration = max(i[1] for i in data)
    models = [lambda x: max(i[0] * (1 - x / (i[1]/max_duration)), 0) for i in data]

    rpc.sleep(WEEK * 4)
    rpc.mine()

    # advance clock a month at a time and compare theoretical weight to actual weights
    while history[-1].timestamp < timestamp + max_duration:
        for i in range(3):
            gauge_controller.enact_vote(i, {'from': accounts[4]})

        relative_time = (history[-1].timestamp - timestamp) / max_duration
        weights = [gauge_controller.gauge_relative_weight(three_gauges[i]) / 1e18 for i in range(3)]

        theoretical_weights = [
            sum((votes[i][0]/10000) * models[i](relative_time) for i in range(3)),
            sum((votes[i][1]/10000) * models[i](relative_time) for i in range(3)),
            sum((votes[i][2]/10000) * models[i](relative_time) for i in range(3)),
        ]
        theoretical_weights = [w and (w / sum(theoretical_weights)) for w in theoretical_weights]

        print(relative_time, weights, theoretical_weights)
        for i in range(3):
            assert abs(weights[i] - theoretical_weights[i]) <= WEEK / YEAR

        rpc.sleep(WEEK * 4)
        rpc.mine()
