# @version 0.2.5
"""
@title Curve Fee Distribution
@author Curve Finance
@license MIT
"""

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

start_time: public(uint256)
time_cursor: public(uint256)
time_cursor_of: public(HashMap[address, uint256])
user_epoch_of: public(HashMap[address, int128])

last_token_time: public(uint256)
tokens_per_week: public(uint256[1000000000000000])
last_distributed: public(HashMap[address, uint256])  # Distributed in the week of time_cursor_of

token: public(address)
total_received: public(uint256)
token_last_balance: public(uint256)

ve_supply: public(uint256[1000000000000000])  # VE total supply at week bounds
ve_balance_of: public(HashMap[address, uint256])


@external
def __init__(_start_time: uint256, _token: address):
    t: uint256 = _start_time / WEEK * WEEK
    self.start_time = t
    self.time_cursor = t
    self.token = _token


@internal
def checkpoint_token():
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
            self.tokens_per_week[this_week] += to_distribute * (block.timestamp - t) / since_last
            break
        else:
            self.tokens_per_week[this_week] += to_distribute * (next_week - t) / since_last
        t = next_week
        this_week = next_week
