# @version 0.2.4
"""
@title Token Distributor
@author Lixir Finance
@license MIT
"""

from vyper.interfaces import ERC20

interface LiquidityGauge:
    # Presumably, other gauges will provide the same interfaces
    def integrate_fraction(addr: address) -> uint256: view
    def user_checkpoint(addr: address) -> bool: nonpayable


interface GaugeController:
    def gauge_types(addr: address) -> int128: view

event UpdateMiningParameters:
    time: uint256
    rate: uint256
    supply: uint256

event Distributed:
    recipient: indexed(address)
    gauge: address
    distributed: uint256


###### CRV20 vars
# General constants
YEAR: constant(uint256) = 86400 * 365


# Supply parameters
RATE_REDUCTION_TIME: constant(uint256) = YEAR
RATE_REDUCTION_COEFFICIENT: constant(uint256) = 2 # half every epoch
INFLATION_DELAY: constant(uint256) = 86400
initial_rate: uint256 # calculated in __init__

# Supply variables
mining_epoch: public(int128)
start_epoch_time: public(uint256)
rate: public(uint256)

start_epoch_supply: uint256
##############

# LIX
lix: public(address)
controller: public(address)

# user -> gauge -> value
distributed: public(HashMap[address, HashMap[address, uint256]])

@external
def __init__(_lix: address, _controller: address, _init_supply: uint256):
    self.lix = _lix
    self.controller = _controller

    # TODO: idk if this is the best way to endow this contract but whatever
    # assert(ERC20(_lix).transferFrom(msg.sender, self, _init_supply))
    self.start_epoch_time = block.timestamp + INFLATION_DELAY - RATE_REDUCTION_TIME
    self.mining_epoch = -1
    self.initial_rate = _init_supply / RATE_REDUCTION_COEFFICIENT / RATE_REDUCTION_TIME
    self.rate = 0


@internal
def _update_mining_parameters():
    """
    @dev Update mining rate and supply at the start of the epoch
         Any modifying mining call must also call this
         Called whenever the previous epoch has concluded
    """
    _rate: uint256 = self.rate
    _start_epoch_supply: uint256 = self.start_epoch_supply

    self.start_epoch_time += RATE_REDUCTION_TIME
    self.mining_epoch += 1

    if _rate == 0:
        _rate = self.initial_rate
    else:
        # TODO test this code. Might be something up with like ofsetting and messing things up
        _start_epoch_supply += _rate / RATE_REDUCTION_COEFFICIENT * RATE_REDUCTION_TIME
        self.start_epoch_supply = _start_epoch_supply
        _rate = _rate / RATE_REDUCTION_COEFFICIENT

    self.rate = _rate

    log UpdateMiningParameters(block.timestamp, _rate, _start_epoch_supply)


@external
def update_mining_parameters():
    """
    @notice Update mining rate and supply at the start of the epoch
    @dev Callable by any address, but only once per epoch
         Total supply becomes slightly larger if this function is called late
    """
    assert block.timestamp >= self.start_epoch_time + RATE_REDUCTION_TIME  # dev: too soon!
    self._update_mining_parameters()


@external
def start_epoch_time_write() -> uint256:
    """
    @notice Get timestamp of the current mining epoch start
            while simultaneously updating mining parameters
    @return Timestamp of the epoch
    """
    _start_epoch_time: uint256 = self.start_epoch_time
    if block.timestamp >= _start_epoch_time + RATE_REDUCTION_TIME:
        self._update_mining_parameters()
        return self.start_epoch_time
    else:
        return _start_epoch_time


@external
def future_epoch_time_write() -> uint256:
    """
    @notice Get timestamp of the next mining epoch start
            while simultaneously updating mining parameters
    @return Timestamp of the next epoch
    """
    _start_epoch_time: uint256 = self.start_epoch_time
    if block.timestamp >= _start_epoch_time + RATE_REDUCTION_TIME:
        self._update_mining_parameters()
        return self.start_epoch_time + RATE_REDUCTION_TIME
    else:
        return _start_epoch_time + RATE_REDUCTION_TIME


# TODO : check this function works properly...I think since I changed around the
# way that mining params get updated, it could fuck up calculations
@external
@view
def mintable_in_timeframe(start: uint256, end: uint256) -> uint256:
    """
    @notice How much supply is mintable from start timestamp till end timestamp
    @param start Start of the time interval (timestamp)
    @param end End of the time interval (timestamp)
    @return Tokens mintable from `start` till `end`
    """
    assert start <= end  # dev: start > end
    to_mint: uint256 = 0
    current_epoch_time: uint256 = self.start_epoch_time
    current_rate: uint256 = self.rate

    # Special case if end is in future (not yet minted) epoch
    if end > current_epoch_time + RATE_REDUCTION_TIME:
        current_epoch_time += RATE_REDUCTION_TIME
        current_rate = current_rate / RATE_REDUCTION_COEFFICIENT

    assert end <= current_epoch_time + RATE_REDUCTION_TIME  # dev: too far in future

    for i in range(999):  # Curve will not work in 1000 years. Darn!
        if end >= current_epoch_time:
            current_end: uint256 = end
            if current_end > current_epoch_time + RATE_REDUCTION_TIME:
                current_end = current_epoch_time + RATE_REDUCTION_TIME

            current_start: uint256 = start
            if current_start >= current_epoch_time + RATE_REDUCTION_TIME:
                break  # We should never get here but what if...
            elif current_start < current_epoch_time:
                current_start = current_epoch_time

            to_mint += current_rate * (current_end - current_start)

            if start >= current_epoch_time:
                break

        current_epoch_time -= RATE_REDUCTION_TIME
        current_rate = current_rate / RATE_REDUCTION_COEFFICIENT # TODO this line might mess up, test it later
        assert current_rate <= self.initial_rate  # This should never happen

    return to_mint


@internal
def _distribute_for(gauge_addr: address, _for: address):
    assert GaugeController(self.controller).gauge_types(gauge_addr) >= 0  # dev: gauge is not added
    assert _for != ZERO_ADDRESS  # dev: zero address

    LiquidityGauge(gauge_addr).user_checkpoint(_for)
    total_dist: uint256 = LiquidityGauge(gauge_addr).integrate_fraction(_for) # TODO: write some tests to make sure the gauges are doing the correct thing here
    to_dist: uint256 = total_dist - self.distributed[_for][gauge_addr]

    if to_dist != 0:
        if block.timestamp >= self.start_epoch_time + RATE_REDUCTION_TIME:
            self._update_mining_parameters()
        ERC20(self.lix).transfer(_for, to_dist)
        self.distributed[_for][gauge_addr] = total_dist

        log Distributed(_for, gauge_addr, total_dist)


@external
@nonreentrant('lock')
def distribute(gauge_addr: address):
    """
    @notice Distribute everything which belongs to `msg.sender` and send to them
    @param gauge_addr `LiquidityGauge` address to get mintable amount from
    """
    self._distribute_for(gauge_addr, msg.sender)


@external
@nonreentrant('lock')
def dist_many(gauge_addrs: address[8]):
    """
    @notice Distribute everything which belongs to `msg.sender` across multiple gauges
    @param gauge_addrs List of `LiquidityGauge` addresses
    """
    for i in range(8):
        if gauge_addrs[i] == ZERO_ADDRESS:
            break
        self._distribute_for(gauge_addrs[i], msg.sender)

