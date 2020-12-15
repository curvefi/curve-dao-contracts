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
integrated_deposit: public(HashMap[address, uint256])
integrated_claimed: public(HashMap[address, uint256])
commited_deposit_for: public(HashMap[address, HashMap[address, uint256]])

@external
def __init__(_gauge: address):
    self.gauge = _gauge


@view
@internal
def _claim_tokens(_coin: address, account: address) -> uint256:
    working_balance:  uint256 = Gauge(self.gauge).working_balances(account)
    working_supply: uint256 = Gauge(self.gauge).working_supply()
    old_commited_deposit_for: uint256 = self.commited_deposit_for[_coin][account]

    avaliable_deposit_amount:uint256 = self.integrated_deposit[_coin] - self.commited_deposit_for[_coin][account] - self.integrated_claimed[_coin]
    if avaliable_deposit_amount == 0:
        return 0

    return avaliable_deposit_amount * working_balance / working_supply


@view
@external
def claim_tokens(_coin: address) -> uint256:
    return self._claim_tokens(_coin, msg.sender)


@external
@nonreentrant('lock')
def deposit(_coin: address, _value: uint256):
    self.integrated_deposit[_coin] += _value
    assert ERC20(_coin).transferFrom(msg.sender, self, _value)

    log Deposit(_coin, _value)


@external
@nonreentrant('lock')
def claim(_coin: address) -> bool:
    available_amount: uint256 = self._claim_tokens(_coin, msg.sender)
    assert available_amount > 0, "already claimed"

    ERC20(_coin).transfer(msg.sender, available_amount)
    self.integrated_claimed[_coin] += available_amount
    self.commited_deposit_for[_coin][msg.sender] = self.integrated_deposit[_coin]

    return True