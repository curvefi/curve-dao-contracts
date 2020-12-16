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
claimable_accounts: public(HashMap[address, HashMap[address, bool]])
total_claimed: public(HashMap[address, uint256])
# old_integrated_inv_supply: public(HashMap[address, uint256])
# new_integrated_inv_supply: public(HashMap[address, uint256])

integrated_claimed: public(HashMap[address, uint256])
claimed_for: public(HashMap[address, HashMap[address, uint256]])

integrated_deposit: public(HashMap[address, uint256])
old_integrated_deposit: public(HashMap[address, uint256])
commited_deposit_for: public(HashMap[address, HashMap[address, uint256]])
current_working_supply: public(HashMap[address, uint256])


# last_working_supply: public(HashMap[address, HashMap[address, uint256]])
# new_integrate_inv: public(HashMap[address, uint256])
# new_working_supply: public(HashMap[address, HashMap[address, uint256]])
# new_fraction: public(HashMap[address, HashMap[address, uint256]])


@external
def __init__(_gauge: address):
    self.gauge = _gauge


@view
@internal
def _claimable_tokens(_coin: address, account: address) -> uint256:
    total_balance: uint256 = ERC20(_coin).balanceOf(self)
    fraction: uint256 = Gauge(self.gauge).integrate_fraction(account)
    old_fraction: uint256 = self.last_fraction[_coin][account]
    integrate_inv: uint256 = Gauge(self.gauge).integrate_inv_supply_of(account)
    old_integrate_inv: uint256 = self.last_integrate_inv[_coin][account]
    working_supply: uint256 = max(self.current_working_supply[_coin], Gauge(self.gauge).working_supply())

    if not self.claimable_accounts[_coin][account]:
        assert False, "claim is not allowed"

    if self.commited_deposit_for[_coin][account] == 0 and self.old_integrated_deposit[_coin] > 0:
        return 0

    if self.integrated_deposit[_coin] == self.commited_deposit_for[_coin][account]:
        return 0

    if fraction == old_fraction:
        return 0

    if integrate_inv == old_integrate_inv:
        return 0

    delta_fraction: uint256 = fraction - old_fraction
    delta_integrate_inv: uint256 = integrate_inv - old_integrate_inv

    claim_amount: uint256 = (self.integrated_deposit[_coin] - self.commited_deposit_for[_coin][account] - (self.integrated_claimed[_coin]) ) * INTEGRATE_INV_SUPPLY_FACTOR * delta_fraction / delta_integrate_inv / working_supply

    if claim_amount > total_balance:
        assert False, "PEPEGA"

    # if claim_amount - self.claimed_for[_coin][account] > total_balance: 
    #    return total_balance

    return claim_amount


@view
@external
def claimable_tokens(_coin: address) -> uint256:
    return self._claimable_tokens(_coin, msg.sender)


@external
@nonreentrant('lock')
def deposit(_coin: address, _value: uint256):
    if _value != 0:
        self.old_integrated_deposit[_coin] = self.integrated_deposit[_coin]
        self.integrated_deposit[_coin] += _value
        self.current_working_supply[_coin] = Gauge(self.gauge).working_supply()
        # self.new_integrated_inv_supply[_coin] = Gauge(self.gauge).integrate_inv_supply(Gauge(self.gauge).period())
        assert ERC20(_coin).transferFrom(msg.sender, self, _value)

    log Deposit(_coin, _value)


@external
@nonreentrant('lock')
def start_claiming(_coin: address) -> bool:
    if (not self.claimable_accounts[_coin][msg.sender]) and Gauge(self.gauge).working_balances(msg.sender) > 0:
        self.claimable_accounts[_coin][msg.sender] = True
        self.last_fraction[_coin][msg.sender] = Gauge(self.gauge).integrate_fraction(msg.sender)
        self.last_integrate_inv[_coin][msg.sender] = Gauge(self.gauge).integrate_inv_supply_of(msg.sender)
        self.commited_deposit_for[_coin][msg.sender] = self.integrated_deposit[_coin]
        return True
    return False


@external
@nonreentrant('lock')
def claim(_coin: address) -> bool:
    if not self.claimable_accounts[_coin][msg.sender]:
        assert False, "claim is not allowed"

    # current_fraction: uint256 = Gauge(self.gauge).integrate_fraction(msg.sender)
    # current_integrate_inv: uint256 = Gauge(self.gauge).integrate_inv_supply_of(msg.sender)
    # # dev: nam pohui 4to ti naclaimil suka)
    # if self.last_fraction[_coin][msg.sender] == 0:
    #     self.last_fraction[_coin][msg.sender] = current_fraction
    #     self.last_integrate_inv[_coin][msg.sender] = current_integrate_inv
    #     self.commited_deposit_for[_coin][msg.sender] = self.integrated_deposit[_coin]

    #     return True

    available_amount: uint256 = self._claimable_tokens(_coin, msg.sender)
    assert available_amount > 0, "already claimed"

    ERC20(_coin).transfer(msg.sender, available_amount)
    self.last_integrate_inv[_coin][msg.sender] = Gauge(self.gauge).integrate_inv_supply_of(msg.sender)
    self.last_fraction[_coin][msg.sender] = Gauge(self.gauge).integrate_fraction(msg.sender)
    self.commited_deposit_for[_coin][msg.sender] = self.integrated_deposit[_coin]
    self.claimed_for[_coin][msg.sender] += available_amount
    self.total_claimed[_coin] += available_amount

    return True