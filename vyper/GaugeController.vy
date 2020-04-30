# The contract which controls gauges and issuance of coins through those

admin: address  # Can and will be a smart contract
token: address  # CRV token

# Gauge parameters
# All numbers are "fixed point" on the basis of 1e18
n_gauge_types: public(int128)
n_gauges: public(int128)

gauges: public(map(int128, address))
gauge_types: public(map(address, int128))
gauge_weights: public(map(address, uint256))
gauge_relative_weights: public(map(address, uint256))

type_weights: public(map(int128, uint256))
weight_sums_per_type: public(map(int128, uint256))
total_weight: public(uint256)

start_epoch_time: public(timestamp)
last_change: public(timestamp)


@public
def __init__(token_address: address):
    self.admin = msg.sender
    self.token = token_address
    self.n_gauge_types = 0
    self.n_gauges = 0
    self.total_weight = 0


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
        _type_weight: uint256 = self.type_weights[gauge_type]
        _total_weight: uint256 = self.total_weight
        self.weight_sums_per_type[gauge_type] += weight
        _total_weight += _type_weight * weight
        self.total_weight = _total_weight
        self.gauge_relative_weights[addr] = 10 ** 18 * _type_weight * weight / _total_weight
        self.last_change = block.timestamp


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
