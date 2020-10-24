# @version 0.2.7
"""
@title Curve Fee Distribution
@author Curve Finance
@license MIT
"""

# XXX TODO
# * events
# * multiple funding addresses
# XXX TODO

from vyper.interfaces import ERC20


interface VotingEscrow:
    def user_point_epoch(addr: address) -> uint256: view
    def epoch() -> uint256: view
    def user_point_history(addr: address, loc: uint256) -> Point: view
    def point_history(loc: uint256) -> Point: view
    def checkpoint(): nonpayable


struct Point:
    bias: int128
    slope: int128  # - dweight / dt
    ts: uint256
    blk: uint256  # block


WEEK: constant(uint256) = 7 * 86400
TOKEN_CHECKPOINT_DEADLINE: constant(uint256) = 86400

start_time: public(uint256)
time_cursor: public(uint256)
time_cursor_of: public(HashMap[address, uint256])
user_epoch_of: public(HashMap[address, uint256])

last_token_time: public(uint256)
tokens_per_week: public(uint256[1000000000000000])

voting_escrow: public(address)
token: public(address)
total_received: public(uint256)
token_last_balance: public(uint256)

ve_supply: public(uint256[1000000000000000])  # VE total supply at week bounds

admin: public(address)
future_admin: public(address)


@external
def __init__(_voting_escrow: address, _start_time: uint256, _token: address, _admin: address):
    t: uint256 = _start_time / WEEK * WEEK
    self.start_time = t
    self.last_token_time = t
    self.time_cursor = t
    self.token = _token
    self.voting_escrow = _voting_escrow
    self.admin = _admin


@external
def set_admin(addr: address):
    assert msg.sender == self.admin  # dev: access denied
    self.future_admin = addr


@external
def apply_admin():
    assert msg.sender == self.admin
    assert self.future_admin != ZERO_ADDRESS
    self.admin = self.future_admin


@external
def checkpoint_token():
    assert msg.sender == self.admin

    token_balance: uint256 = ERC20(self.token).balanceOf(self)
    to_distribute: uint256 = token_balance - self.token_last_balance
    self.token_last_balance = token_balance

    t: uint256 = self.last_token_time
    since_last: uint256 = block.timestamp - t
    self.last_token_time = block.timestamp
    this_week: uint256 = t / WEEK * WEEK
    next_week: uint256 = 0

    for i in range(20):
        next_week = this_week + WEEK
        if block.timestamp < next_week:
            if since_last == 0 and block.timestamp == t:
                self.tokens_per_week[this_week] += to_distribute
            else:
                self.tokens_per_week[this_week] += to_distribute * (block.timestamp - t) / since_last
            break
        else:
            if since_last == 0 and next_week == t:
                self.tokens_per_week[this_week] += to_distribute
            else:
                self.tokens_per_week[this_week] += to_distribute * (next_week - t) / since_last
        t = next_week
        this_week = next_week


@internal
def find_timestamp_epoch(ve: address, _timestamp: uint256) -> uint256:
    _min: uint256 = 0
    _max: uint256 = VotingEscrow(ve).epoch()
    for i in range(128):
        if _min >= _max:
            break
        _mid: uint256 = (_min + _max + 1) / 2
        pt: Point = VotingEscrow(ve).point_history(_mid)
        if pt.ts <= _timestamp:
            _min = _mid
        else:
            _max = _mid - 1
    return _min


@internal
def _checkpoint_total_supply():
    ve: address = self.voting_escrow
    t: uint256 = self.time_cursor
    rounded_timestamp: uint256 = block.timestamp / WEEK * WEEK

    for i in range(20):
        if t > rounded_timestamp:
            break
        else:
            epoch: uint256 = self.find_timestamp_epoch(ve, t)
            pt: Point = VotingEscrow(ve).point_history(epoch)
            dt: int128 = 0
            if t > pt.ts:
                # If the point is at 0 epoch, it can actually be earlier than the first deposit
                # Then make dt 0
                dt = convert(t - pt.ts, int128)
            self.ve_supply[t] = convert(max(pt.bias - pt.slope * dt, 0), uint256)
        t += WEEK

    self.time_cursor = t


@external
def checkpoint_total_supply():
    self._checkpoint_total_supply()


@external
@nonreentrant('lock')
def claim(addr: address = msg.sender) -> uint256:
    ve: address = self.voting_escrow
    last_token_time: uint256 = self.last_token_time

    if block.timestamp >= self.time_cursor:
        self._checkpoint_total_supply()

    last_token_time = last_token_time / WEEK * WEEK

    # Minimal user_epoch is 0 (if user had no point)
    user_epoch: uint256 = 0
    max_user_epoch: uint256 = VotingEscrow(ve).user_point_epoch(addr)
    _start_time: uint256 = self.start_time

    if max_user_epoch == 0:
        # No lock = no fees
        return 0

    if self.time_cursor_of[addr] == 0:
        # Need to do the initial binary search
        _min: uint256 = 0
        _max: uint256 = max_user_epoch
        for i in range(128):
            if _min >= _max:
                break
            _mid: uint256 = (_min + _max + 1) / 2
            pt: Point = VotingEscrow(ve).user_point_history(addr, _mid)
            if pt.ts <= _start_time:
                _min = _mid
            else:
                _max = _mid - 1
        user_epoch = _min
    else:
        user_epoch = self.user_epoch_of[addr]

    if user_epoch == 0:
        user_epoch = 1

    user_point: Point = VotingEscrow(ve).user_point_history(addr, user_epoch)
    week_cursor: uint256 = self.time_cursor_of[addr]
    if week_cursor == 0:
        week_cursor = (user_point.ts + WEEK - 1) / WEEK * WEEK
    if week_cursor >= last_token_time:
        return 0
    if week_cursor < _start_time:
        week_cursor = _start_time
    old_user_point: Point = empty(Point)
    to_distribute: uint256 = 0

    # Iterate over weeks
    for i in range(50):
        if week_cursor >= last_token_time:
            break

        if week_cursor >= user_point.ts and user_epoch <= max_user_epoch:
            user_epoch += 1
            old_user_point = user_point
            if user_epoch > max_user_epoch:
                user_point = empty(Point)
            else:
                user_point = VotingEscrow(ve).user_point_history(addr, user_epoch)

        else:
            # Calc
            dt: int128 = convert(week_cursor - old_user_point.ts, int128)
            balance_of: uint256 = convert(max(old_user_point.bias - dt * old_user_point.slope, 0), uint256)
            if balance_of == 0 and user_epoch > max_user_epoch:
                break
            if balance_of > 0:
                to_distribute += balance_of * self.tokens_per_week[week_cursor] / self.ve_supply[week_cursor]

            week_cursor += WEEK

    self.user_epoch_of[addr] = min(max_user_epoch, user_epoch)
    self.time_cursor_of[addr] = week_cursor

    if to_distribute > 0:
        token: address = self.token
        assert ERC20(token).transfer(addr, to_distribute)
        self.token_last_balance = ERC20(token).balanceOf(self)

    return to_distribute
