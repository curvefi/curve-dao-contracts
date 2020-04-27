# This gauge can be used for measuring liquidity and insurance
from vyper.interfaces import ERC20

contract CRV20:
    def current_rate() -> uint256: constant
    def previous_rate() -> uint256: constant
    def start_epoch_time() -> timestamp: constant


token: public(address)
balanceOf: public(map(address, uint256))
totalSupply: public(uint256)

# The goal is to be able to calculate ∫(rate * balance / totalSupply dt) from 0 till checkpoint
# All values are kept in units of being multiplied by 1e18
epoch_checkpoints: map(int128, timestamp) # Beginning of the epoch
last_epoch: int128

# 1e18 * ∫(rate(t) / totalSupply(t) dt) from 0 till checkpoint
integrate_inv_supply: map(int128, uint256)  # bump epoch when rate() changes
integrate_checkpoint: timestamp

# 1e18 * ∫(rate(t) / totalSupply(t) dt) from (last_action) till checkpoint
integrate_inv_supply_of: map(address, uint256)
integrate_checkpoint_of: map(address, timestamp)


# ∫(balance * rate(t) / totalSupply(t) dt) from 0 till checkpoint
integrate_fraction: public(map(address, uint256))

inflation_rate: uint256

# XXX also set_weight_fraction and integrate with * (weight / sum(all_weights))


@public
def __init__(addr: address):
    self.token = addr
    self.totalSupply = 0
    self.integrate_checkpoint = block.timestamp
    self.integrate_inv_supply[0] = 0
    self.epoch_checkpoints[0] = block.timestamp
    self.last_epoch_checkpoint = 0
    self.inflation_rate = CRV20(addr).current_rate()


@private
def checkpoint(addr: address, old_value: uint256, old_supply: uint256):
    _integrate_checkpoint: timestamp = self.integrate_checkpoint
    if block.timestamp > _integrate_checkpoint:
        _token: address = self.token
        epoch: int128 = self.last_epoch
        new_epoch_time: timestamp = CRV20(_token).start_epoch_time()  # XXX updated epoch time instead, this is LAGGING
        _integrate_inv_supply: uint256 = self.integrate_inv_supply[epoch]
        rate: uint256 = self.inflation_rate

        dt: uint = 0
        if new_epoch_time > _integrate_checkpoint:
            # Handle going across epochs
            # No less than one checkpoint is expected in 1 year
            dt = as_unitless_number(new_epoch_time - _integrate_checkpoint)
            _integrate_inv_supply += 10 ** 18 * rate * dt / old_supply
            rate = CRV20(_token).current_rate()
            self.inflation_rate = rate
            epoch += 1
            self.last_epoch = epoch
            dt = as_unitless_number(block.timestamp - new_epoch_time)
        else:
            dt = as_unitless_number(block.timestamp - _integrate_checkpoint)
        _integrate_inv_supply += 10 ** 18 * rate * dt / old_supply

        # Need to handle going across (multiple) epochs
        # if old_value > 0:
        #     _integrate_inv_supply_of: uint256 = self.integrate_inv_supply_of[addr]
        #     self.integrate_fraction[addr] += old_value * (_integrate_inv_supply - _integrate_inv_supply_of) / 10 ** 18

        self.integrate_inv_supply[epoch] = _integrate_inv_supply
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
