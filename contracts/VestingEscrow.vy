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


token: public(address)
start_time: public(uint256)
end_time: public(uint256)
initial_locked: public(HashMap[address, uint256])
total_claimed: public(HashMap[address, uint256])

initial_locked_supply: public(uint256)

can_disable: public(bool)
disabled: public(HashMap[address, bool])
disabled_at: public(HashMap[address, uint256])

admin: public(address)


@external
def __init__(_token: address, _start_time: uint256, _end_time: uint256, _can_disable: bool):
    """
    @param _token Address of the ERC20 token being distributed
    @param _start_time Timestamp at which the distribution starts. Should be in
        the future, so that we have enough time to VoteLock everyone
    @param _end_time Time until everything should be vested
    @param _can_disable Whether admin can disable accounts in this deployment
    """
    assert _start_time >= block.timestamp
    assert _end_time > _start_time

    self.token = _token
    self.admin = msg.sender
    self.start_time = _start_time
    self.end_time = _end_time
    self.can_disable = _can_disable

# TODO:
# * set admin (commit / transfer ownership w/o wait)
# * make a contract which gets funded and can create and fund new VestedEscrow
#   contracts with 1 user in each (factory)


@external
@nonreentrant('lock')
def fund(_recipients: address[10], _amounts: uint256[10]):
    assert msg.sender == self.admin

    # Transfer tokens for all of the recipients here
    _total_amount: uint256 = 0
    for i in range(10):
        if _recipients[i] == ZERO_ADDRESS:
            break
        _total_amount += _amounts[i]
    self.initial_locked_supply += _total_amount
    assert ERC20(self.token).transferFrom(msg.sender, self, _total_amount)

    # Create individual records
    for i in range(10):
        if _recipients[i] == ZERO_ADDRESS:
            break
        self.initial_locked[_recipients[i]] = _amounts[i]

        log Fund(_recipients[i], _amounts[i])


@external
def toggle_disable(_recipient: address):
    assert msg.sender == self.admin
    assert self.can_disable, "Cannot disable"

    is_disabled: bool = not self.disabled[_recipient]
    self.disabled[_recipient] = is_disabled
    if is_disabled:
        self.disabled_at[_recipient] = block.timestamp

    log ToggleDisable(_recipient, is_disabled)


@external
def disable_can_disable(_recipient: address):
    assert msg.sender == self.admin
    self.can_disable = False


@internal
@view
def _total_vested_of(_recipient: address, _time: uint256 = 0) -> uint256:
    start: uint256 = self.start_time
    end: uint256 = self.end_time
    locked: uint256 = self.initial_locked[_recipient]
    t: uint256 = _time
    if t == 0:
        t = block.timestamp
    return min(locked * (t - start) / (end - start), locked)


@internal
@view
def _total_vested() -> uint256:
    start: uint256 = self.start_time
    end: uint256 = self.end_time
    locked: uint256 = self.initial_locked_supply
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


@internal
def _claim_for(addr: address):
    t: uint256 = block.timestamp
    if self.disabled[addr]:
        t = self.disabled_at[addr]
    claimable: uint256 = self._total_vested_of(addr, t) - self.total_claimed[addr]
    self.total_claimed[addr] += claimable
    assert ERC20(self.token).transfer(addr, claimable)

    log Claim(claimable)


@external
@nonreentrant('lock')
def claim(addr: address = ZERO_ADDRESS):
    if addr == ZERO_ADDRESS:
        self._claim_for(msg.sender)
    else:
        self._claim_for(addr)
