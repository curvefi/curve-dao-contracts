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
    def integrate_inv_supply(period: uint256) -> uint256: view
    def working_supply() -> uint256: view
    def period() -> uint256: view


INTEGRATE_INV_SUPPLY_FACTOR: constant(uint256) = 10 ** 18

gauge: public(address)
# last_fraction: public(HashMap[address, HashMap[address, uint256]])
# last_integrate_inv: public(HashMap[address, uint256])
total_claimed: public(HashMap[address, uint256])
claimed_for: public(HashMap[address, HashMap[address, uint256]])
working_supply_for: public(HashMap[address, HashMap[address, uint256]])
    

@external
def __init__(_gauge: address):
    self.gauge = _gauge


@view
@internal
def _claim_tokens(_coin: address, account: address) -> uint256:
    total_balance: uint256 = ERC20(_coin).balanceOf(self)
    fraction: uint256 = Gauge(self.gauge).integrate_fraction(account)
    # old_fraction: uint256 = self.last_fraction[_coin][account]
    integrate_inv: uint256 = Gauge(self.gauge).integrate_inv_supply(Gauge(self.gauge).period())
    # old_integrate_inv: uint256 = self.last_integrate_inv[account]
    working_supply: uint256 = Gauge(self.gauge).working_supply()
    old_working_supply: uint256 = self.working_supply_for[_coin][account]

    if working_supply <= old_working_supply:
        return 0

    # claim_amount: uint256 = (total_balance + self.total_claimed[_coin]) * fraction * INTEGRATE_INV_SUPPLY_FACTOR / integrate_inv / working_supply
    # claim_amount: uint256 = total_balance * (fraction - old_fraction) * INTEGRATE_INV_SUPPLY_FACTOR / (integrate_inv - old_integrate_inv) / working_supply
    # claim_amount: uint256 = (total_balance + self.total_claimed[_coin]) * fraction * INTEGRATE_INV_SUPPLY_FACTOR / integrate_inv / working_supply
    claim_amount: uint256 = (total_balance + self.total_claimed[_coin]) * fraction * INTEGRATE_INV_SUPPLY_FACTOR / integrate_inv / (working_supply - old_working_supply)
    already_claimed: uint256 = self.claimed_for[_coin][account]

    if claim_amount > total_balance: 
        return 0

    if claim_amount <= already_claimed: 
        return 0

    return claim_amount - already_claimed


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
    self.working_supply_for[_coin][msg.sender] = Gauge(self.gauge).working_supply()
    self.total_claimed[_coin] += available_amount
    self.claimed_for[_coin][msg.sender] += available_amount
    # self.last_integrate_inv[_coin] = Gauge(self.gauge).integrate_inv_supply(Gauge(self.gauge).period())
    # self.last_fraction[_coin][msg.sender] = Gauge(self.gauge).integrate_fraction(msg.sender)
    return True