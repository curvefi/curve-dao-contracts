from vyper.interfaces import ERC20

event Fund:
    recipient: indexed(address)
    amount: uint256
    start_time: uint256
    time: uint256
    can_disable: bool

event Claim:
    claimed: uint256

event ToggleDisable:
    recipient: address
    disabled: bool


token: public(address)
default_start_time: public(uint256)
start_time: public(HashMap[address, uint256])
end_time: public(HashMap[address, uint256])
initial_locked: public(HashMap[address, uint256])
total_claimed: public(HashMap[address, uint256])

can_disable: public(HashMap[address, bool])
disabled: public(HashMap[address, bool])

admin: public(address)


@external
def __init__(_token: address, _start_time: uint256):
    """
    @param _token Address of the ERC20 token being distributed
    @param _start_time Timestamp at which the distribution starts. Should be in
        the future, so that we have enough time to VoteLock everyone
    """
    self.token = _token
    self.admin = msg.sender
    self.default_start_time = _start_time

# XXX include data to calculate locked and unlocked total supply
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
        assert _times[i] > default_start, "Time is not in the future"
        self.initial_locked[_recipients[i]] = _amounts[i]
        self.start_time[_recipients[i]] = default_start
        self.end_time[_recipients[i]] = _times[i]

        log Fund(_recipients[i], _amounts[i], default_start, _times[i], False)


@external
@nonreentrant('lock')
def fund_individual(_recipient: address, _amount: uint256,
                    _start_time: uint256, _time: uint256, _can_disable: bool):
    assert msg.sender == self.admin

    default_start: uint256 = self.default_start_time
    t0: uint256 = _start_time
    if t0 == 0:
        t0 = default_start
    else:
        assert t0 >= default_start
    assert _time > t0, "Time is not in the future"

    assert ERC20(self.token).transferFrom(msg.sender, self, _amount)

    if _can_disable:
        # Typically for employees
        self.can_disable[_recipient] = True
    self.initial_locked[_recipient] = _amount
    self.start_time[_recipient] = t0
    self.end_time[_recipient] = _time

    log Fund(_recipient, _amount, default_start, _time, _can_disable)


@external
def toggle_disable(_recipient: address):
    assert msg.sender == self.admin

    if self.can_disable[_recipient]:
        is_disabled: bool = not self.disabled[_recipient]
        self.disabled[_recipient] = is_disabled

        log ToggleDisable(_recipient, is_disabled)


@external
def disable_can_disable(_recipient: address):
    assert msg.sender == self.admin
    self.can_disable[_recipient] = False


@internal
@view
def _total_vested(_recipient: address) -> uint256:
    start: uint256 = self.start_time[_recipient]
    end: uint256 = self.end_time[_recipient]
    locked: uint256 = self.initial_locked[_recipient]
    return min(locked * (block.timestamp - start) / (end - start), locked)


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
    if self.can_disable[msg.sender]:
        assert not self.disabled[msg.sender], "Vesting was frozen"
    claimable: uint256 = self._total_vested(msg.sender) - self.total_claimed[msg.sender]
    self.total_claimed[msg.sender] += claimable
    assert ERC20(self.token).transfer(msg.sender, claimable)

    log Claim(claimable)
