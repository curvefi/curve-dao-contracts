# The contract which controls gauges and issuance of coins through those

admin: address  # Can and will be a smart contract
token: address  # CRV token

# Gauge parameters
# All numbers are "fixed point" on the basis of 1e18
n_gauge_types: public(int128)
n_gauges: public(int128)

# Every time a weight changes, period increases
# The idea is: relative weights are guaranteed to not change within the period
# Period 0 is reserved for "not started" (b/c default value in maps)
period: public(int128)
period_timestamp: public(map(int128, timestamp))

gauges: public(map(int128, address))
gauge_types: public(map(address, int128))

gauge_weights: map(address, map(int128, uint256))  # address -> period -> weight
type_weights: map(int128, map(int128, uint256))  # type_id -> period -> weight
weight_sums_per_type: map(int128, map(int128, uint256))  # type_id -> period -> weight
total_weight: map(int128, uint256)  # period -> total_weight

type_last: map(int128, int128)  # Last period for type update type_id -> period
gauge_last: map(address, int128)  # Last period for gauge update gauge_addr -> period
# Total is always at the last updated state


@public
def __init__(token_address: address):
    self.admin = msg.sender
    self.token = token_address
    self.n_gauge_types = 0
    self.n_gauges = 0
    self.period = 0
    self.period_timestamp[0] = block.timestamp


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
    # If someone adds the same gauge twice, it will override the previous one
    # That's probably ok

    n: int128 = self.n_gauges
    self.n_gauges = n + 1

    self.gauges[n] = addr
    self.gauge_types[addr] = gauge_type

    if weight > 0:
        p: int128 = self.period + 1
        self.period = p
        l: int128 = self.type_last[gauge_type]
        self.type_last[gauge_type] = p
        self.gauge_last[addr] = p
        old_sum: uint256 = self.weight_sums_per_type[gauge_type][l]
        _type_weight: uint256 = self.type_weights[gauge_type][l]
        if l > 0:
            # Fill historic type weights and sums
            _p: int128 = l
            for i in range(500):  # If higher (unlikely) - 0 weights
                _p += 1
                if _p == p:
                    break
                self.type_weights[gauge_type][_p] = _type_weight
                self.weight_sums_per_type[gauge_type][_p] = old_sum
        self.type_weights[gauge_type][p] = _type_weight
        self.gauge_weights[addr][p] = weight
        self.weight_sums_per_type[gauge_type][p] = weight + old_sum
        self.total_weight[p] = self.total_weight[p-1] + _type_weight * weight
        self.period_timestamp[p] = block.timestamp


@public
@constant
def gauge_relative_weight(addr: address, _period: int128=-1) -> uint256:
    p: int128 = _period
    if _period < 0:
        p = self.period
    _total_weight: uint256 = self.total_weight[p]
    if _total_weight > 0:
        gauge_type: int128 = self.gauge_types[addr]
        tl: int128 = self.type_last[gauge_type]
        gl: int128 = self.gauge_last[addr]
        if p < tl:
            tl = p
        if p < gl:
            gl = p
        return 10 ** 18 * self.type_weights[gauge_type][tl] * self.gauge_weights[addr][gl] / _total_weight
    else:
        return 0


@public
def change_type_weight(type_id: int128, weight: uint256):
    assert msg.sender == self.admin

    p: int128 = self.period + 1
    self.period = p
    l: int128 = self.type_last[type_id]
    self.type_last[type_id] = p
    old_weight: uint256 = self.type_weights[type_id][l]
    old_sum: uint256 = self.weight_sums_per_type[type_id][l]
    old_total_weight: uint256 = self.total_weight[p-1]

    if l > 0:
        # Fill historic type weights and sums
        _p: int128 = l
        for i in range(500):  # If higher (unlikely) - 0 weights
            _p += 1
            if _p == p:
                break
            self.type_weights[type_id][_p] = old_weight
            self.weight_sums_per_type[type_id][_p] = old_sum

    self.total_weight[p] = old_total_weight + old_sum * weight - old_sum * old_weight
    self.type_weights[type_id][p] = weight
    self.weight_sums_per_type[type_id][p] = old_sum

    self.period_timestamp[p] = block.timestamp


@public
def change_gauge_weight(addr: address, weight: uint256):
    assert msg.sender == self.admin

    # Fill weight from gauge_last to now, type_sums from type_last till now, total
    gauge_type: int128 = self.gauge_types[addr]
    p: int128 = self.period + 1
    self.period = p
    gl: int128 = self.gauge_last[addr]
    tl: int128 = self.type_last[gauge_type]
    old_gauge_weight: uint256 = self.gauge_weights[addr][gl]
    type_weight: uint256 = self.type_weights[gauge_type][tl]
    old_sum: uint256 = self.weight_sums_per_type[gauge_type][tl]
    old_total: uint256 = self.total_weight[p-1]

    if tl > 0:
        _p: int128 = tl
        for i in range(500):
            _p += 1
            if _p == p:
                break
            self.type_weights[gauge_type][_p] = type_weight
            self.weight_sums_per_type[gauge_type][_p] = old_sum
    self.type_weights[gauge_type][p] = type_weight
    self.type_last[gauge_type] = p

    if gl > 0:
        _p: int128 = gl
        for i in range(500):
            _p += 1
            if _p == p:
                break
            self.gauge_weights[addr][_p] = old_gauge_weight
    self.gauge_last[addr] = p

    new_sum: uint256 = old_sum + weight - old_gauge_weight
    self.gauge_weights[addr][p] = weight
    self.weight_sums_per_type[gauge_type][p] = new_sum
    self.total_weight[p] = old_total + new_sum * type_weight - old_sum * type_weight

    self.period_timestamp[p] = block.timestamp


@public
def last_change() -> timestamp:
    return self.period_timestamp[self.period]


@public
def get_gauge_weight(addr: address) -> uint256:
    return self.gauge_weights[addr][self.gauge_last[addr]]


@public
def get_type_weight(type_id: int128) -> uint256:
    return self.type_weights[type_id][self.type_last[type_id]]


@public
def get_total_weight() -> uint256:
    return self.total_weight[self.period]


@public
def get_weights_sum_per_type(type_id: int128) -> uint256:
    return self.weight_sums_per_type[type_id][self.type_last[type_id]]
