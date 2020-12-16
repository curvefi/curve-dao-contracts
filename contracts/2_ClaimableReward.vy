# @version 0.2.4
"""
@title Claimable Reward
@author Curve Finance
@license MIT
@notice Used for share reward
"""


from vyper.interfaces import ERC20


interface Gauge:
    def working_supply() -> uint256: view
    def working_balances(account: address) -> uint256: view


event Deposit:
    coin: indexed(address)
    value: uint256

gauge: public(address)
current_deposit: public(HashMap[address, uint256])
current_working_supply: public(HashMap[address, uint256])
current_claimed: public(HashMap[address, uint256])
integrated_deposit: public(HashMap[address, uint256])
integrated_claimed: public(HashMap[address, uint256])
claimed_for: public(HashMap[address, HashMap[address, uint256]])
commited_deposit_for: public(HashMap[address, HashMap[address, uint256]])

@external
def __init__(_gauge: address):
    self.gauge = _gauge


@view
@internal
def _claimable_tokens(_coin: address, account: address) -> uint256:
    working_balance:  uint256 = Gauge(self.gauge).working_balances(account)
    working_supply: uint256 = Gauge(self.gauge).working_supply()
    old_commited_deposit_for: uint256 = self.commited_deposit_for[_coin][account]

    # if self.integrated_deposit[_coin] == self.commited_deposit_for[_coin][account] + self.integrated_claimed[_coin]:
    #     return 0

    if self.integrated_deposit[_coin] == self.commited_deposit_for[_coin][account]:
        return 0

    working_supply = max(working_supply, self.current_working_supply[_coin])

    # avaliable_deposit_amount:uint256 = self.integrated_deposit[_coin] - self.commited_deposit_for[_coin][account] - (self.integrated_claimed[_coin] - self.claimed_for[_coin][account])
    available_amount: uint256 = ERC20(_coin).balanceOf(self)
    claim_amount: uint256 = self.current_deposit[_coin] * working_balance / working_supply

    if claim_amount >= available_amount:
        return available_amount

    return claim_amount 


@view
@external
def claimable_tokens(_coin: address) -> uint256:
    return self._claimable_tokens(_coin, msg.sender)


@external
@nonreentrant('lock')
def deposit(_coin: address, _value: uint256):
    self.current_deposit[_coin] = self.current_deposit[_coin] + _value - self.current_claimed[_coin] # or ERC20(_coin).balanceOf(self) + _value
    self.current_claimed[_coin] = 0
    self.integrated_deposit[_coin] += _value
    self.current_working_supply[_coin] = Gauge(self.gauge).working_supply()
    assert ERC20(_coin).transferFrom(msg.sender, self, _value)

    log Deposit(_coin, _value)


@external
@nonreentrant('lock')
def claim(_coin: address) -> bool:
    available_amount: uint256 = self._claimable_tokens(_coin, msg.sender)
    assert available_amount > 0, "already claimed"

    ERC20(_coin).transfer(msg.sender, available_amount)
    self.current_claimed[_coin] += available_amount
    self.integrated_claimed[_coin] += available_amount
    self.claimed_for[_coin][msg.sender] += available_amount 
    self.commited_deposit_for[_coin][msg.sender] = self.integrated_deposit[_coin]

    return True