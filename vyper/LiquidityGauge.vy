# This gauge can be used for measuring liquidity and insurance
from vyper.interfaces import ERC20

# This is not required at all, but let's define here for commentary purposes
contract LiquidityGauge:
    def balanceOf(addr: address) -> uint256: constant
    def totalSupply() -> uint256: constant
    def integrate_fraction(addr: address, start: uint256, end: uint256) -> uint256: constant


token: public(address)
balanceOf: public(map(address, uint256))
totalSupply: public(uint256)

# The goal is to be able to calculate ∫(balance/totalSupply dt) from 0 till checkpoint
# For that, we keep:

# 1e36 * ∫(1/totalSupply dt) from 0 till checkpoint
integrate_inv_supply: public(uint256)

# 1e36 * ∫(1/totalSupply dt) from (last_action) till checkpoint
integrate_inv_supply_of: public(map(address, uint256))

integrate_checkpoint: public(timestamp)

# 1e18 * ∫(balance/totalSupply dt) from 0 till checkpoint
integrate_fraction: public(map(address, uint256))

# XXX also set_weight_fraction and integrate with * (weight / sum(all_weights))


@public
def __init__(addr: address):
    self.token = addr
    self.totalSupply = 0
    self.integrate_inv_supply = 0
    self.integrate_checkpoint = block.timestamp


@private
def checkpoint(addr: address, old_value: uint256, old_supply: uint256):
    dt: uint256 = as_unitless_number(block.timestamp - self.integrate_checkpoint)
    if dt > 0:
        _integrate_inv_supply: uint256 = self.integrate_inv_supply + 10 ** 36 * dt / old_supply

        if old_value > 0:
            _integrate_inv_supply_of: uint256 = self.integrate_inv_supply_of[addr]
            self.integrate_fraction[addr] += old_value * (_integrate_inv_supply - _integrate_inv_supply_of)

        self.integrate_inv_supply = _integrate_inv_supply
        self.integrate_inv_supply_of[addr] = _integrate_inv_supply
        self.integrate_checkpoint = block.timestamp


@public
@nonreentrant('lock')
def deposit(value: uint256):
    old_value: uint256 = self.balanceOf[msg.sender]
    old_supply: uint256 = self.totalSupply

    self.checkpoint(msg.sender, old_value, old_supply)

    self.balanceOf[msg.sender] = old_value + value
    self.totalSupply = old_supply + value

    assert_modifiable(ERC20(self.token).transferFrom(msg.sender, self, value))
    # XXX logs


@public
@nonreentrant('lock')
def withdraw(value: uint256):
    old_value: uint256 = self.balanceOf[msg.sender]
    old_supply: uint256 = self.totalSupply

    self.checkpoint(msg.sender, old_value, old_supply)

    self.balanceOf[msg.sender] = old_value - value
    self.totalSupply = old_supply - value

    assert_modifiable(ERC20(self.token).transfer(msg.sender, value))
    # XXX logs
