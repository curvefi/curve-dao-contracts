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
INITIAL_RATE: constant(uint256) = 274_815_283 * 10 ** 18 / YEAR  # leading to 43% premine
RATE_REDUCTION_TIME: constant(uint256) = YEAR
RATE_REDUCTION_COEFFICIENT: constant(uint256) = 1189207115002721024  # 2 ** (1/4) * 1e18
RATE_DENOMINATOR: constant(uint256) = 10 ** 18
INFLATION_DELAY: constant(uint256) = 86400

# Supply variables
mining_epoch: public(int128)
start_epoch_time: public(uint256)
rate: public(uint256)

start_epoch_supply: uint256
##############

# LIX
token: public(address)
controller: public(address)

# user -> gauge -> value
distributed: public(HashMap[address, HashMap[address, uint256]])

@external
def __init__(_token: address, _controller: address, init_supply: uint256):
    self.token = _token
    self.controller = _controller

    # TODO: idk if this is the best way to endow this contract but whatever
    assert(ERC20(self.token).transferFrom(msg.sender, self, init_supply))

    self.start_epoch_time = block.timestamp + INFLATION_DELAY - RATE_REDUCTION_TIME
    self.mining_epoch = -1
    self.rate = 0
    self.start_epoch_supply = init_supply


@external
@view
def totalBalance() -> uint256:
    return ERC20(self.token).balanceOf(self)


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
        _rate = INITIAL_RATE
    else:
        _start_epoch_supply += _rate * RATE_REDUCTION_TIME
        self.start_epoch_supply = _start_epoch_supply
        _rate = _rate * RATE_DENOMINATOR / RATE_REDUCTION_COEFFICIENT

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
        current_rate = current_rate * RATE_DENOMINATOR / RATE_REDUCTION_COEFFICIENT

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
        current_rate = current_rate * RATE_REDUCTION_COEFFICIENT / RATE_DENOMINATOR  # double-division with rounding made rate a bit less => good
        assert current_rate <= INITIAL_RATE  # This should never happen

    return to_mint


@internal
def _distribute_for(gauge_addr: address, _for: address):
    assert GaugeController(self.controller).gauge_types(gauge_addr) >= 0  # dev: gauge is not added
    assert _for != ZERO_ADDRESS  # dev: zero address

    # TODO this seems kinda sus...not really clicking for me how gauges are doing their thing...
    # seems like things could break pretty easily if we don't set it up properly...
    LiquidityGauge(gauge_addr).user_checkpoint(_for)
    total_dist: uint256 = LiquidityGauge(gauge_addr).integrate_fraction(_for)
    to_dist: uint256 = total_dist - self.distributed[_for][gauge_addr]

    if to_dist != 0:
        if block.timestamp >= self.start_epoch_time + RATE_REDUCTION_TIME:
            self._update_mining_parameters()
        ERC20(self.token).transfer(_for, to_dist)
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

