# @version 0.2.4
"""
@title Claimable Reward
@author Curve Finance
@license MIT
@notice Used for share reward
"""


from vyper.interfaces import ERC20


interface Gauge:
    def integrate_fraction(_address: address) -> uint256: view
    # def integrate_inv_supply_of(_address: address) -> uint256: view
    def integrate_inv_supply(period: uint256) -> uint256: view
    # def working_balances(_address: address) -> uint256: view
    def working_supply() -> uint256: view
    def period() -> uint256: view


gauge: public(address)
    

@external
def __init__(_gauge: address):
    self.gauge = _gauge


@view
@internal
def _claim_tokens(_coin: address, account: address) -> uint256:
    total_balance: uint256 = ERC20(_coin).balanceOf(self)
    fraction: uint256 = Gauge(self.gauge).integrate_fraction(account)
    integrate_inv: uint256 = Gauge(self.gauge).integrate_inv_supply(Gauge(self.gauge).period())
    working_supply: uint256 = Gauge(self.gauge).working_supply()
    return total_balance * fraction * 10 ** 18 / integrate_inv / working_supply


@view
@external
def claim_tokens(_coin: address) -> uint256:
    return self._claim_tokens(_coin, msg.sender)


@external
@nonreentrant('lock')
def claim(_coin: address) -> bool:
    available_amount: uint256 = self._claim_tokens(_coin, msg.sender)
    assert available_amount > 0, "already claimed"

    ERC20(_coin).transfer(msg.sender, available_amount)
    return True