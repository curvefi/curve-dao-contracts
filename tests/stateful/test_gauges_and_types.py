import pytest

from brownie.test import strategy


class StateMachine:

    st_type = strategy('decimal', min_value=0, max_value="0.99999999")
    st_gauge_weight =strategy('uint', min_value= 10**17, max_value = 10**19)
    st_type_weight = strategy('uint', min_value= 10**17, max_value = 10**19)


    def __init__(self, LiquidityGauge, accounts, gauge_controller, mock_lp_token, minter):
        self.LiquidityGauge = LiquidityGauge
        self.accounts = accounts

        self.lp_token = mock_lp_token
        self.minter = minter
        self.controller = gauge_controller

    def setup(self):
        self.type_weights = []
        self.gauges = []


    def initialize_add_type(self, st_type_weight):
        self.rule_add_type(st_type_weight)

    def rule_add_gauge(self, st_type, st_gauge_weight):
        if not self.type_weights:
            return
        gauge_type = int(st_type*(len(self.type_weights)))
        gauge = self.LiquidityGauge.deploy(self.lp_token, self.minter, {'from': self.accounts[0]})

        self.controller.add_gauge(gauge, gauge_type, st_gauge_weight, {'from': self.accounts[0]})
        self.gauges.append({'contract': gauge, 'type': gauge_type, 'weight': st_gauge_weight})

    def rule_add_type(self, st_type_weight):
        self.controller.add_type(b"Type!", st_type_weight, {'from': self.accounts[0]})
        self.type_weights.append(st_type_weight)

    def _gauge_weight(self, idx):
        return sum(i['weight'] for i in self.gauges if i['type'] == idx)

    def invariant_gauge_weight_sums(self):
        for idx in range(len(self.type_weights)):
            gauge_weight_sum = self._gauge_weight(idx)
            assert self.controller.get_weights_sum_per_type(idx) == gauge_weight_sum

    def invariant_total_type_weight(self):
        total_weight = sum(self._gauge_weight(idx) * weight for idx, weight in enumerate(self.type_weights))
        assert self.controller.get_total_weight() == total_weight

    def invariant_relative_gauge_weight(self):
        total_weight = sum(self._gauge_weight(idx) * weight for idx, weight in enumerate(self.type_weights))
        for gauge, weight, idx in [(i['contract'], i['weight'], i['type']) for i in self.gauges]:
            assert self.controller.gauge_relative_weight(gauge) == 10**18 * self.type_weights[idx] * weight // total_weight


def test_gauge(state_machine, LiquidityGauge, accounts, gauge_controller, mock_lp_token, minter):
    state_machine(StateMachine, LiquidityGauge, accounts, gauge_controller, mock_lp_token, minter)
