# @version 0.2.4
"""
@title Staking Burner
@author Curve Finance
@license MIT
@notice Used for share profit
"""


from vyper.interfaces import ERC20

interface Gauge:
    def integrate_fraction(_address: address) -> uint256: view


PROFIT_DIVIDER: constant(uint256) = 2


pool_proxy: public(address)
gauge: public(address)
last_integrate_fraction: public(HashMap[address, uint256])


@external
def __init__(_pool_proxy: address, _gauge: address):
    self.pool_proxy = _pool_proxy
    self.gauge = _gauge


@external
@nonreentrant('lock')
def burn_coin(_coin: address) -> bool:
    profit: uint256 = ERC20(_coin).balanceOf(self.pool_proxy)
    last_fraction: uint256 = Gauge(self.gauge).integrate_fraction(msg.sender)
    profit = profit * (last_fraction - self.last_integrate_fraction[msg.sender]) / PROFIT_DIVIDER
    
    ERC20(_coin).transferFrom(ZERO_ADDRESS , msg.sender, profit)
    self.last_integrate_fraction[msg.sender] = last_fraction

    return True
