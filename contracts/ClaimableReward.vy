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
    def integrate_inv_supply_of(_address: address) -> uint256: view
    def period() -> uint256: view


gauge: public(address)
total_claimed: public(HashMap[address, uint256])
claimed_of: public(HashMap[address, HashMap[address, uint256]])
integrate_fraction: public(HashMap[address, HashMap[address, uint256]])
integrate_inv_supply: public(HashMap[address, HashMap[address, uint256]])
    

@external
def __init__(_gauge: address):
    self.gauge = _gauge


@view
@internal
def _claim_tokens(_coin: address, account: address) -> uint256:
    current_fraction: uint256 = Gauge(self.gauge).integrate_fraction(account)
    last_fraction: uint256 = self.integrate_fraction[_coin][account]
    
    if current_fraction <= last_fraction:
        return 0

    total_balance: uint256 = ERC20(_coin).balanceOf(self)
    current_integrate_inv: uint256 = Gauge(self.gauge).integrate_inv_supply_of(account)
    last_integrate_inv: uint256 = self.integrate_inv_supply[_coin][account]

    total_claim_of: uint256 = total_balance * (current_fraction - last_fraction) / (current_integrate_inv - last_integrate_inv)
    if total_claim_of <= self.claimed_of[_coin][account]: 
        return 0

    return total_claim_of - self.claimed_of[_coin][account]


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
    self.total_claimed[_coin] += available_amount
    self.claimed_of[_coin][msg.sender] += available_amount

    self.integrate_fraction[_coin][msg.sender] = Gauge(self.gauge).integrate_fraction(msg.sender)
    self.integrate_inv_supply[_coin][msg.sender] = Gauge(self.gauge).integrate_inv_supply_of(msg.sender)

    return True