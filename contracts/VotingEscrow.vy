# Voting escrow to have time-weighted votes
# The idea: votes have a weight depending on time, so that users are committed
# to the future of (whatever they are voting for).
# The weight in this implementation is linear, and lock cannot be more than maxtime:
# w ^
# 1 +        /
#   |      /
#   |    /
#   |  /
#   |/
# 0 +--------+------> time
#       maxtime (4 years?)

struct Point:
    bias: int128
    slope: int128  # - dweight / dt
    ts: uint256
    blk: uint256  # block
# We cannot really do block numbers per se b/c slope is per time, not per block
# and per block could be fairly bad b/c Ethereum changes blocktimes.
# What we can do is to extrapolate ***At functions

struct LockedBalance:
    amount: int128
    end: uint256


interface ERC20:
    def decimals() -> uint256: view
    def name() -> String[64]: view
    def symbol() -> String[32]: view
    def transfer(to: address, amount: uint256) -> bool: nonpayable
    def transferFrom(spender: address, to: address, amount: uint256) -> bool: nonpayable


event Deposit:
    provider: indexed(address)
    value: uint256
    locktime: indexed(uint256)

event Withdraw:
    provider: indexed(address)
    value: uint256


WEEK: constant(uint256) = 604800  # 7 * 86400 seconds - all future times are rounded by week
MAXTIME: constant(uint256) = 126144000  # 4 * 365 * 86400 - 4 years

token: public(address)
supply: public(uint256)

locked: public(HashMap[address, LockedBalance])

epoch: public(uint256)
point_history: public(Point[100000000000000000000000000000])  # epoch -> unsigned point
user_point_history: public(HashMap[address, Point[1000000000]])  # user -> Point[user_epoch]
user_point_epoch: public(HashMap[address, uint256])
slope_changes: public(HashMap[uint256, int128])  # time -> signed slope change

# Aragon's view methods for compatibility
controller: public(address)
transfersEnabled: public(bool)

name: public(String[64])
symbol: public(String[32])
version: public(String[32])
decimals: public(uint256)

# Whitelisted (smart contract) wallets which are allowed to deposit
# The goal is to prevent tokenizing the escrow
contracts_whitelist: public(HashMap[address, bool])  # When sets?
admin: address  # Can and will be a smart contract


@external
def __init__(token_addr: address, _name: String[64], _symbol: String[32], _version: String[32]):
    self.admin = msg.sender
    self.token = token_addr
    self.point_history[0].blk = block.number
    self.point_history[0].ts = block.timestamp
    self.controller = msg.sender
    self.transfersEnabled = True
    self.decimals = ERC20(token_addr).decimals()
    self.name = _name
    self.symbol = _symbol
    self.version = _version


@external
def transfer_ownership(addr: address):
    assert msg.sender == self.admin
    self.admin = addr


@external
def add_to_whitelist(addr: address):
    assert msg.sender == self.admin
    self.contracts_whitelist[addr] = True


@external
def remove_from_whitelist(addr: address):
    assert msg.sender == self.admin
    self.contracts_whitelist[addr] = False


@internal
def assert_not_contract(addr: address):
    if addr != tx.origin:
        assert self.contracts_whitelist[addr], "Smart contract depositors not allowed"


@external
@view
def get_last_user_slope(addr: address) -> int128:
    uepoch: uint256 = self.user_point_epoch[addr]
    return self.user_point_history[addr][uepoch].slope


@internal
def _checkpoint(addr: address, old_locked: LockedBalance, new_locked: LockedBalance):
    u_old: Point = empty(Point)
    u_new: Point = empty(Point)
    _epoch: uint256 = self.epoch

    # Calculate slopes and biases
    # Kept at zero when they have to
    if old_locked.end > block.timestamp and old_locked.amount > 0:
        u_old.slope = old_locked.amount / MAXTIME
        u_old.bias = u_old.slope * convert(old_locked.end - block.timestamp, int128)
    if new_locked.end > block.timestamp and new_locked.amount > 0:
        u_new.slope = new_locked.amount / MAXTIME
        u_new.bias = u_new.slope * convert(new_locked.end - block.timestamp, int128)

    # Read values of scheduled changes in the slope
    # old_locked.end can be in the past and in the future
    # new_locked.end can ONLY by in the FUTURE unless everything expired: than zeros
    old_dslope: int128 = self.slope_changes[old_locked.end]
    new_dslope: int128 = 0
    if new_locked.end != 0:
        if new_locked.end == old_locked.end:
            new_dslope = old_dslope
        else:
            new_dslope = self.slope_changes[new_locked.end]

    last_point: Point = Point({bias: 0, slope: 0, ts: block.timestamp, blk: block.number})
    if _epoch > 0:
        last_point = self.point_history[_epoch]
    last_checkpoint: uint256 = last_point.ts
    # initial_last_point is used for extrapolation to calculate block number
    # (approximately, for *At methods) and save them
    # as we cannot figure that out exactly from inside the contract
    initial_last_point: Point = last_point
    block_slope: uint256 = 0  # dblock/dt
    if block.timestamp > last_point.ts:
        block_slope = 10 ** 18 * (block.number - last_point.blk) / (block.timestamp - last_point.ts)
    # If last point is already recorded in this block, slope=0
    # But that's ok b/c we know the block in such case

    # Go over weeks to fill history and calculate what the current point is
    t_i: uint256 = (last_checkpoint / WEEK) * WEEK
    for i in range(255):
        # Hopefully it won't happen that this won't get used in 5 years!
        # If it does, users will be able to withdraw but vote weight will be broken
        t_i += WEEK
        d_slope: int128 = 0
        if t_i > block.timestamp:
            t_i = block.timestamp
        else:
            d_slope = self.slope_changes[t_i]
        last_point.bias -= last_point.slope * convert(t_i - last_checkpoint, int128)
        last_point.slope += d_slope
        if last_point.bias < 0:  # This can happen
            last_point.bias = 0
        if last_point.slope < 0:  # This cannot happen - just in case
            last_point.slope = 0
        last_checkpoint = t_i
        last_point.ts = t_i
        last_point.blk = initial_last_point.blk + block_slope * (t_i - initial_last_point.ts) / 10 ** 18
        _epoch += 1
        if t_i == block.timestamp:
            last_point.blk = block.number
            break
        else:
            self.point_history[_epoch] = last_point

    self.epoch = _epoch
    # Now point_history is filled until t=now

    # If last point was in this block, the slope change has been applied already
    # But in such case we have 0 slope(s)
    last_point.slope += (u_new.slope - u_old.slope)
    last_point.bias += (u_new.bias - u_old.bias)
    if last_point.slope < 0:
        last_point.slope = 0
    if last_point.bias < 0:
        last_point.bias = 0

    # Record the changed point into history
    self.point_history[_epoch] = last_point

    # Schedule the slope changes (slope is going down)
    # We subtract new_user_slope from [new_locked.end]
    # and add old_user_slope to [old_locked.end]
    if old_locked.end > block.timestamp:
        # old_dslope was <something> - u_old.slope, so we cancel that
        old_dslope += u_old.slope
        if new_locked.end == old_locked.end:
            old_dslope -= u_new.slope  # It was a new deposit, not extension
        self.slope_changes[old_locked.end] = old_dslope

    if new_locked.end > block.timestamp:
        if new_locked.end > old_locked.end:
            new_dslope -= u_new.slope  # old slope disappeared at this point
            self.slope_changes[new_locked.end] = new_dslope
        # else: we recorded it already in old_dslope

    # Now handle user history
    user_epoch: uint256 = self.user_point_epoch[addr] + 1

    self.user_point_epoch[addr] = user_epoch
    u_new.ts = block.timestamp
    u_new.blk = block.number
    self.user_point_history[addr][user_epoch] = u_new


@internal
def _deposit_for(_addr: address, _value: uint256, _unlock_time: uint256):
    unlock_time: uint256 = (_unlock_time / WEEK) * WEEK  # Locktime is rounded down to weeks
    _locked: LockedBalance = self.locked[_addr]  # How much is locked previously and for how long

    if unlock_time == 0:
        # Checks needed if we are not extending the lock
        # It means that a workable lock should already exist
        assert _locked.amount > 0, "No existing lock found"
        assert _locked.end > block.timestamp, "Cannot add to expired lock. Withdraw"
        assert _value != 0  # Why add zero to existing lock

    else:
        # Lock is extended, or a new one is created, with deposit added or not
        if _locked.end <= block.timestamp:
            assert _locked.amount == 0, "Withdraw old tokens first"
        assert unlock_time >= _locked.end, "Cannot decrease the lock duration"
        assert unlock_time > block.timestamp, "Can only lock until time in the future"
        assert unlock_time <= block.timestamp + MAXTIME, "Voting lock can be 4 years max"
        if (_locked.end <= block.timestamp) or (unlock_time == _locked.end):
            # If lock is not extended, we must be adding more to it
            assert _value != 0
        assert unlock_time <= block.timestamp + MAXTIME, "Voting lock can be 4 years max"

    self.supply += _value
    old_locked: LockedBalance = _locked
    # Adding to existing lock, or if a lock is expired - creating a new one
    _locked.amount += convert(_value, int128)
    if unlock_time != 0:
        _locked.end = unlock_time
    self.locked[_addr] = _locked

    # Possibilities:
    # Both old_locked.end could be current or expired (>/< block.timestamp)
    # value == 0 (extend lock) or value > 0 (add to lock or extend lock)
    # _locked.end > block.timestamp (always)
    self._checkpoint(_addr, old_locked, _locked)

    if _value != 0:
        assert ERC20(self.token).transferFrom(_addr, self, _value)

    log Deposit(_addr, _value, _locked.end)


@external
@nonreentrant('lock')
def deposit_for(_addr: address, _value: uint256):
    """
    Anyone can deposit for someone else, but cannot extend their locktime
    """
    assert self.user_point_epoch[_addr] != 0, "First tx should be done by user"
    self._deposit_for(_addr, _value, 0)


@external
@nonreentrant('lock')
def deposit(_value: uint256, _unlock_time: uint256 = 0):
    """
    Deposit `value` or extend locktime
    If previous lock is expired but hasn't been taken - use that
    """
    self.assert_not_contract(msg.sender)
    self._deposit_for(msg.sender, _value, _unlock_time)


@external
@nonreentrant('lock')
def withdraw(_value: uint256 = 0):
    """
    Withdraw `value` if it's withdrawable
    """
    self.assert_not_contract(msg.sender)
    _locked: LockedBalance = self.locked[msg.sender]
    assert block.timestamp >= _locked.end, "The lock didn't expire"
    value: uint256 = _value
    if value == 0:
        value = convert(_locked.amount, uint256)

    old_locked: LockedBalance = _locked
    _locked.end = 0
    _locked.amount -= convert(value, int128)
    assert _locked.amount >= 0, "Withdrawing more than you have"
    self.locked[msg.sender] = _locked
    self.supply -= value

    # old_locked can have either expired <= timestamp or zero end
    # _locked has only 0 end
    # Both can have >= 0 amount
    self._checkpoint(msg.sender, old_locked, _locked)

    assert ERC20(self.token).transfer(msg.sender, value)

    log Withdraw(msg.sender, value)


# The following ERC20/minime-compatible methods are not real balanceOf and supply!
# They measure the weights for the purpose of voting, so they don't represent
# real coins.
@internal
@view
def find_block_epoch(_block: uint256, max_epoch: uint256) -> uint256:
    # Binary search
    _min: uint256 = 0
    _max: uint256 = max_epoch
    for i in range(128):  # Will be always enough for 128-bit numbers
        if _min >= _max:
            break
        _mid: uint256 = (_min + _max + 1) / 2
        if self.point_history[_mid].blk <= _block:
            _min = _mid
        else:
            _max = _mid - 1
    return _min


@external
@view
def balanceOf(addr: address) -> uint256:
    _epoch: uint256 = self.user_point_epoch[addr]
    if _epoch == 0:
        return 0
    else:
        last_point: Point = self.user_point_history[addr][_epoch]
        last_point.bias -= last_point.slope * convert(block.timestamp - last_point.ts, int128)
        if last_point.bias < 0:
            last_point.bias = 0
        return convert(last_point.bias, uint256)


@external
@view
def balanceOfAt(addr: address, _block: uint256) -> uint256:
    # Copying and pasting totalSupply code because Vyper cannot pass by
    # reference yet
    assert _block <= block.number

    # Binary search
    _min: uint256 = 0
    _max: uint256 = self.user_point_epoch[addr]
    for i in range(128):  # Will be always enough for 128-bit numbers
        if _min >= _max:
            break
        _mid: uint256 = (_min + _max + 1) / 2
        if self.user_point_history[addr][_mid].blk <= _block:
            _min = _mid
        else:
            _max = _mid - 1

    upoint: Point = self.user_point_history[addr][_min]

    max_epoch: uint256 = self.epoch
    _epoch: uint256 = self.find_block_epoch(_block, max_epoch)
    point_0: Point = self.point_history[_epoch]
    d_block: uint256 = 0
    d_t: uint256 = 0
    if _epoch < max_epoch:
        point_1: Point = self.point_history[_epoch + 1]
        d_block = point_1.blk - point_0.blk
        d_t = point_1.ts - point_0.ts
    else:
        d_block = block.number - point_0.blk
        d_t = block.timestamp - point_0.ts
    block_time: uint256 = point_0.ts
    if d_block != 0:
        block_time += d_t * (_block - point_0.blk) / d_block

    upoint.bias -= upoint.slope * convert(block_time - upoint.ts, int128)
    if upoint.bias >= 0:
        return convert(upoint.bias, uint256)
    else:
        return 0


@internal
@view
def supply_at(point: Point, t: uint256) -> uint256:
    last_point: Point = point
    t_i: uint256 = (last_point.ts / WEEK) * WEEK
    for i in range(255):
        t_i += WEEK
        d_slope: int128 = 0
        if t_i > t:
            t_i = t
        else:
            d_slope = self.slope_changes[t_i]
        last_point.bias -= last_point.slope * convert(t_i - last_point.ts, int128)
        if t_i == t:
            break
        last_point.slope += d_slope
        last_point.ts = t_i

    if last_point.bias < 0:
        last_point.bias = 0
    return convert(last_point.bias, uint256)


@external
@view
def totalSupply() -> uint256:
    _epoch: uint256 = self.epoch
    last_point: Point = self.point_history[_epoch]
    return self.supply_at(last_point, block.timestamp)


@external
@view
def totalSupplyAt(_block: uint256) -> uint256:
    assert _block <= block.number
    _epoch: uint256 = self.epoch
    target_epoch: uint256 = self.find_block_epoch(_block, _epoch)

    point: Point = self.point_history[target_epoch]
    dt: uint256 = 0
    if target_epoch < _epoch:
        point_next: Point = self.point_history[target_epoch + 1]
        if point.blk != point_next.blk:
            dt = (_block - point.blk) * (point_next.ts - point.ts) / (point_next.blk - point.blk)
    else:
        if point.blk != block.number:
            dt = (_block - point.blk) * (block.timestamp - point.ts) / (block.number - point.blk)
    # Now dt contains info on how far are we beyond point

    return self.supply_at(point, point.ts + dt)


# Dummy methods for compatibility with Aragon

@external
def changeController(_newController: address):
    assert msg.sender == self.controller
    self.controller = _newController
