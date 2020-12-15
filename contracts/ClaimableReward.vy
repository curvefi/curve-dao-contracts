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
    def integrate_inv_supply_of(account: address) -> uint256: view
    def working_supply() -> uint256: view
    def working_balances(account: address) -> uint256: view
    def period() -> uint256: view


event Deposit:
    coin: indexed(address)
    value: uint256

INTEGRATE_INV_SUPPLY_FACTOR: constant(uint256) = 10 ** 18

gauge: public(address)
last_fraction: public(HashMap[address, HashMap[address, uint256]])
last_integrate_inv: public(HashMap[address, HashMap[address, uint256]])
last_integrate_inv_for_deposit: public(HashMap[address, uint256])
# total_claimed: public(HashMap[address, uint256])
# old_integrated_inv_supply: public(HashMap[address, uint256])
# new_integrated_inv_supply: public(HashMap[address, uint256])

integrated_deposit: public(HashMap[address, uint256])
commited_deposit_for: public(HashMap[address, HashMap[address, uint256]])

claimed_for: public(HashMap[address, HashMap[address, uint256]])
# last_working_supply: public(HashMap[address, HashMap[address, uint256]])
# new_integrate_inv: public(HashMap[address, uint256])
# new_working_supply: public(HashMap[address, HashMap[address, uint256]])
# new_fraction: public(HashMap[address, HashMap[address, uint256]])


@external
def __init__(_gauge: address):
    self.gauge = _gauge


@view
@internal
def _claim_tokens(_coin: address, account: address) -> uint256:
    total_balance: uint256 = ERC20(_coin).balanceOf(self)
    fraction: uint256 = Gauge(self.gauge).integrate_fraction(account)
    old_fraction: uint256 = self.last_fraction[_coin][account]
    integrate_inv: uint256 = Gauge(self.gauge).integrate_inv_supply_of(account)
    old_integrate_inv: uint256 = self.last_integrate_inv[_coin][account]
    working_supply: uint256 = Gauge(self.gauge).working_supply()
    working_balances:  uint256 = Gauge(self.gauge).working_balances(account)
    # old_working_supply: uint256 = self.last_working_supply[_coin][account]

    if fraction <= old_fraction:
        return 0

    # if integrate_inv <= old_integrate_inv:
    #     return 0

    # if working_supply <= old_working_supply:
    #     return 0

    # claim_amount: uint256 = (total_balance + self.total_claimed[_coin]) * fraction * INTEGRATE_INV_SUPPLY_FACTOR / integrate_inv / working_supply
    # claim_amount: uint256 = total_balance * (fraction - old_fraction) * INTEGRATE_INV_SUPPLY_FACTOR / (integrate_inv - old_integrate_inv) / working_supply
    # claim_amount: uint256 = (total_balance + self.total_claimed[_coin]) * fraction * INTEGRATE_INV_SUPPLY_FACTOR / integrate_inv / working_supply
    
    # last_deposit_for: uint256 = self.commited_deposit_for[_coin][account]
    # if last_deposit_for == 0

    # if old_integrate_inv == 0 and Gauge(self.gauge).period() > 1 :
    #     old_integrate_inv = self.last_integrate_inv_for_deposit[_coin]

    delta_fraction: uint256 = fraction - old_fraction
    delta_deposit: uint256 = self.integrated_deposit[_coin] - self.commited_deposit_for[_coin][account]
    delta_integrate_inv: uint256 = integrate_inv - old_integrate_inv

    # if integrate_inv > old_integrate_inv:
    #     delta_integrate_inv = integrate_inv - old_integrate_inv
    # else:
    #     delta_integrate_inv = old_integrate_inv - integrate_inv

    claim_amount: uint256 =  delta_deposit * delta_fraction * INTEGRATE_INV_SUPPLY_FACTOR / delta_integrate_inv / working_supply

    # claim_amount: uint256 = (total_balance + self.total_claimed[_coin]) * working_balances / working_supply # fraction / integrate_inv # * # INTEGRATE_INV_SUPPLY_FACTOR # / integrate_inv # / working_supply
    #already_claimed: uint256 = self.claimed_for[_coin][account]

    #if claim_amount <= already_claimed: 
    #    return 0

    if claim_amount > total_balance: 
       return total_balance # or total_balance ???

    return claim_amount
    # return (fraction - old_fraction) / (integrate_inv - old_integrate_inv)

    # claim_amount: uint256 = (total_balance + self.total_claimed[_coin]) * (fraction - old_fraction) / (integrate_inv - old_integrate_inv) # / (working_supply - old_working_supply)
    

    # if claim_amount > total_balance: 
    #     return 0

    # if claim_amount <= already_claimed: 
    #     return 0

    # return claim_amount - already_claimed


@view
@external
def claim_tokens(_coin: address) -> uint256:
    return self._claim_tokens(_coin, msg.sender)

@external
@nonreentrant('lock')
def deposit(_coin: address, _value: uint256):
    """
    @notice Deposit `_value` `_coin` tokens
    @param _value Number of tokens to deposit
    @param _coin Token for deposit
    """

    if _value != 0:
        self.integrated_deposit[_coin] += _value
        # self.old_integrated_inv_supply[_coin] = self.new_integrated_inv_supply[_coin]
        # self.new_integrated_inv_supply[_coin] = Gauge(self.gauge).integrate_inv_supply(Gauge(self.gauge).period())
        assert ERC20(_coin).transferFrom(msg.sender, self, _value)

    log Deposit(_coin, _value)

@external
@nonreentrant('lock')
def claim(_coin: address) -> bool:
    available_amount: uint256 = self._claim_tokens(_coin, msg.sender)
    # assert available_amount > 0, "already claimed"

    if available_amount > 0:
        ERC20(_coin).transfer(msg.sender, available_amount)
    # self.working_supply_for[_coin][msg.sender] = Gauge(self.gauge).working_supply()
   # self.total_claimed[_coin] += available_amount
    #self.claimed_for[_coin][msg.sender] += available_amount
    self.last_integrate_inv[_coin][msg.sender] = Gauge(self.gauge).integrate_inv_supply(Gauge(self.gauge).period())
    self.last_fraction[_coin][msg.sender] = Gauge(self.gauge).integrate_fraction(msg.sender)
    self.commited_deposit_for[_coin][msg.sender] = self.integrated_deposit[_coin]
    # self.last_working_supply[_coin][msg.sender] = Gauge(self.gauge).working_supply()
    return True