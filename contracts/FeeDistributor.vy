# @version 0.2.6
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
token: public(address)


@external
def __init__(_start_time: uint256, _token: address):
    self.start_time = _start_time / WEEK * WEEK
    self.token = _token
