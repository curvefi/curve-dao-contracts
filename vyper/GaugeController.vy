# The contract which controls gauges and issuance of coins through those

contract CRV20:
    def start_epoch_time_write() -> timestamp: modifying


YEAR: constant(uint256) = 86400 * 365
RATE_REDUCTION_TIME: constant(uint256) = YEAR


admin: address  # Can and will be a smart contract
token: address  # CRV token

# Gauge parameters
# All numbers are "fixed point" on the basis of 1e18
n_gauge_types: public(int128)
n_gauges: public(int128)

gauges: public(map(int128, address))
gauge_types: public(map(address, int128))
gauge_weights: public(map(address, uint256))

type_weights: public(map(int128, uint256))
weight_sums_per_type: public(map(int128, uint256))
total_weight: public(uint256)

start_epoch_time: public(timestamp)  # Last epoch
last_change: public(timestamp)  # Not including change of epoch if any


@public
def __init__(token_address: address):
    self.admin = msg.sender
    self.token = token_address
    self.n_gauge_types = 0
    self.n_gauges = 0
    self.total_weight = 0
    self.last_change = block.timestamp
    self.start_epoch_time = CRV20(token_address).start_epoch_time_write()


@public
def transfer_ownership(addr: address):
    assert msg.sender == self.admin
    self.admin = addr


@public
def add_type():
    assert msg.sender == self.admin
    n: int128 = self.n_gauge_types
    self.n_gauge_types = n + 1
    # maps contain 0 values by default, no need to do anything
    # zero weights don't change other weights - no need to change last_change


@public
def add_gauge(addr: address, gauge_type: int128, weight: uint256 = 0):
    assert msg.sender == self.admin
    assert (gauge_type >= 0) and (gauge_type < self.n_gauge_types)

    n: int128 = self.n_gauges
    self.n_gauges += 1

    self.gauges[n] = addr
    self.gauge_types[addr] = gauge_type
    self.gauge_weights[addr] = weight

    if weight > 0:
        self.weight_sums_per_type[gauge_type] += weight
        self.total_weight += self.type_weights[gauge_type] * weight
        self.last_change = block.timestamp


@public
@constant
def gauge_relative_weight(addr: address) -> uint256:
    return 10 ** 18 * self.type_weights[self.gauge_types[addr]] * self.gauge_weights[addr] / self.total_weight


@public
def change_type_weight(type_id: int128, weight: uint256):
    assert msg.sender == self.admin

    old_weight: uint256 = self.type_weights[type_id]
    old_total_weight: uint256 = self.total_weight
    _weight_sums_per_type: uint256 = self.weight_sums_per_type[type_id]

    self.total_weight = old_total_weight + _weight_sums_per_type * weight - _weight_sums_per_type * old_weight
    self.type_weights[type_id] = weight

    self.last_change = block.timestamp


@public
def change_gauge_weight(addr: address, weight: uint256):
    assert msg.sender == self.admin

    gauge_type: int128 = self.gauge_types[addr]
    type_weight: uint256 = self.type_weights[gauge_type]
    old_weight_sums: uint256 = self.weight_sums_per_type[gauge_type]
    old_total_weight: uint256 = self.total_weight
    old_weight: uint256 = self.gauge_weights[addr]

    weight_sums: uint256 = old_weight_sums + weight - old_weight
    self.gauge_weights[addr] = weight
    self.weight_sums_per_type[gauge_type] = weight_sums
    self.total_weight = old_total_weight + weight_sums * type_weight - old_weight_sums * type_weight

    self.last_change = block.timestamp


@public
def last_change_write() -> timestamp:
    _start_epoch_time: timestamp = self.start_epoch_time
    _last_change: timestamp = self.last_change

    # Bump last epoch if it was changed
    if block.timestamp >= _start_epoch_time + RATE_REDUCTION_TIME:
        _start_epoch_time = CRV20(self.token).start_epoch_time_write()
        self.start_epoch_time = _start_epoch_time

    if _last_change >= _start_epoch_time:
        return _last_change
    else:
        return _start_epoch_time
