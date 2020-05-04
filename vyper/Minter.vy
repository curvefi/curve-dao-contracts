from vyper.interfaces import ERC20

contract CRV20:
    def start_epoch_time_write() -> timestamp: modifying
    def rate() -> uint256: constant

contract Controller:
    def period() -> int128: constant
    def period_write() -> int128: modifying
    def period_timestamp(p: int128) -> timestamp: constant
    def gauge_relative_weight(addr: address, _period: int128) -> uint256: constant
    def gauge_relative_weight_write(addr: address) -> uint256: modifying

token: public(address)
controller: public(address)
admin: public(address)


@public
def __init__(_token: address, _controller: address):
    self.token = _token
    self.controller = _controller
    self.admin = msg.sender


@public
def set_admin(_admin: address):
    assert msg.sender == self.admin
    self.admin = _admin
