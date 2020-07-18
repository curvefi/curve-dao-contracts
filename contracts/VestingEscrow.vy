from vyper.interfaces import ERC20


token: public(address)
default_start_time: public(uint256)
start_time: public(HashMap[address, uint256])
end_time: public(HashMap[address, uint256])
initial_locked: public(HashMap[address, uint256])
total_claimed: public(HashMap[address, uint256])

admin: public(address)


@external
def __init__(_token: address):
    self.token = _token
    self.admin = msg.sender
    self.default_start_time = block.timestamp

# XXX include data to calculate locked and unlocked total supply
# XXX include admin-only trigger for freezing employees
# XXX start_time per user at init - for future employees
# XXX set admin (DAO?)
# XXX events


@external
@nonreentrant('lock')
def fund(_recipients: address[10], _amounts: uint256[10], _times: uint256[10]):
    assert msg.sender == self.admin
    default_start: uint256 = self.default_start_time

    # Transfer tokens for all of the recipients here
    _total_amount: uint256 = 0
    for i in range(10):
        if _recipients[i] == ZERO_ADDRESS:
            break
        _total_amount += _amounts[i]
    assert ERC20(self.token).transferFrom(msg.sender, self, _total_amount)

    # Create individual records
    for i in range(10):
        if _recipients[i] == ZERO_ADDRESS:
            break
        assert _times[i] > block.timestamp, "Time is not in the future"
        self.initial_locked[_recipients[i]] = _amounts[i]
        self.start_time[_recipients[i]] = default_start
        self.end_time[_recipients[i]] = _times[i]


@internal
@view
def _total_vested(_recipient: address) -> uint256:
    start: uint256 = self.start_time[_recipient]
    end: uint256 = self.end_time[_recipient]
    locked: uint256 = self.initial_locked[_recipient]
    return max(locked * (block.timestamp - start) / (end - start), locked)


@external
@view
def vestedOf(_recipient: address) -> uint256:
    return self._total_vested(_recipient)


@external
@view
def balanceOf(_recipient: address) -> uint256:
    return self._total_vested(_recipient) - self.total_claimed[_recipient]


@external
@view
def lockedOf(_recipient: address) -> uint256:
    return self.initial_locked[_recipient] - self._total_vested(_recipient)


@external
@nonreentrant('lock')
def claim():
    claimable: uint256 = self._total_vested(msg.sender) - self.total_claimed[msg.sender]
    self.total_claimed[msg.sender] += claimable
    assert ERC20(self.token).transfer(msg.sender, claimable)
