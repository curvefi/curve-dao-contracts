# @version 0.2.3
from vyper.interfaces import ERC20

event Fund:
    recipient: indexed(address)
    amount: uint256

event Claim:
    claimed: uint256

event ToggleDisable:
    recipient: address
    disabled: bool

event CommitOwnership:
    admin: address

event ApplyOwnership:
    admin: address


token: public(address)
start_time: public(uint256)
end_time: public(uint256)
initial_locked: public(HashMap[address, uint256])
total_claimed: public(HashMap[address, uint256])

initial_locked_supply: public(uint256)

can_disable: public(bool)
disabled_at: public(HashMap[address, uint256])

admin: public(address)
future_admin: public(address)


@external
@nonreentrant('lock')
def initialize(_admin: address, _token: address, _recipient: address, _amount: uint256, _start_time: uint256, _end_time: uint256, _can_disable: bool) -> bool:
    """
    @param _token Address of the ERC20 token being distributed
    @param _start_time Timestamp at which the distribution starts. Should be in
        the future, so that we have enough time to VoteLock everyone
    @param _end_time Time until everything should be vested
    @param _can_disable Whether admin can disable accounts in this deployment
    """
    assert self.admin == ZERO_ADDRESS  # dev: can only initialize once

    assert _start_time >= block.timestamp  # dev: start before now
    assert _end_time > _start_time  # dev: end before start

    self.token = _token
    self.admin = msg.sender
    self.start_time = _start_time
    self.end_time = _end_time
    self.can_disable = _can_disable

    assert ERC20(_token).transferFrom(msg.sender, self, _amount)

    self.initial_locked[_recipient] = _amount
    self.initial_locked_supply = _amount
    log Fund(_recipient, _amount)

    return True


@external
def toggle_disable(_recipient: address):
    assert msg.sender == self.admin  # dev: admin only
    assert self.can_disable, "Cannot disable"

    is_disabled: bool = self.disabled_at[_recipient] == 0
    if is_disabled:
        self.disabled_at[_recipient] = block.timestamp
    else:
        self.disabled_at[_recipient] = 0

    log ToggleDisable(_recipient, is_disabled)


@external
def disable_can_disable():
    assert msg.sender == self.admin  # dev: admin only
    self.can_disable = False


@internal
@view
def _total_vested_of(_recipient: address, _time: uint256 = block.timestamp) -> uint256:
    start: uint256 = self.start_time
    end: uint256 = self.end_time
    locked: uint256 = self.initial_locked[_recipient]
    if _time < start:
        return 0
    return min(locked * (_time - start) / (end - start), locked)


@internal
@view
def _total_vested() -> uint256:
    start: uint256 = self.start_time
    end: uint256 = self.end_time
    locked: uint256 = self.initial_locked_supply
    if block.timestamp < start:
        return 0
    return min(locked * (block.timestamp - start) / (end - start), locked)


@external
@view
def vestedSupply() -> uint256:
    return self._total_vested()


@external
@view
def lockedSupply() -> uint256:
    return self.initial_locked_supply - self._total_vested()


@external
@view
def vestedOf(_recipient: address) -> uint256:
    return self._total_vested_of(_recipient)


@external
@view
def balanceOf(_recipient: address) -> uint256:
    return self._total_vested_of(_recipient) - self.total_claimed[_recipient]


@external
@view
def lockedOf(_recipient: address) -> uint256:
    return self.initial_locked[_recipient] - self._total_vested_of(_recipient)


@external
@nonreentrant('lock')
def claim(addr: address = msg.sender):
    t: uint256 = self.disabled_at[addr]
    if t == 0:
        t = block.timestamp
    claimable: uint256 = self._total_vested_of(addr, t) - self.total_claimed[addr]
    self.total_claimed[addr] += claimable
    assert ERC20(self.token).transfer(addr, claimable)

    log Claim(claimable)


@external
def commit_transfer_ownership(addr: address) -> bool:
    """
    @notice Transfer ownership of GaugeController to `addr`
    @param addr Address to have ownership transferred to
    """
    assert msg.sender == self.admin  # dev: admin only
    self.future_admin = addr
    log CommitOwnership(addr)

    return True


@external
def apply_transfer_ownership() -> bool:
    """
    @notice Apply pending ownership transfer
    """
    assert msg.sender == self.admin  # dev: admin only
    _admin: address = self.future_admin
    self.admin = _admin
    log ApplyOwnership(_admin)

    return True
