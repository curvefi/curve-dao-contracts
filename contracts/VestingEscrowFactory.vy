# @version 0.2.3

from vyper.interfaces import ERC20

interface VestingEscrowSimple:
    def initialize(
        _admin: address,
        _token: address,
        _recipient: address,
        _amount: uint256,
        _start_time: uint256,
        _end_time: uint256,
        _can_disable: bool
    ) -> bool: nonpayable


event CommitOwnership:
    admin: address

event ApplyOwnership:
    admin: address


admin: public(address)
future_admin: public(address)
target: public(address)

@external
def __init__(_target: address):
    self.target = _target
    self.admin = msg.sender


@external
def deploy_vesting_contract(
    _token: address,
    _recipient: address,
    _amount: uint256,
    _start_time: uint256,
    _end_time: uint256,
    _can_disable: bool
) -> address:

    # TODO restrictions on vesting parameters?
    _contract: address = create_forwarder_to(self.target)
    ERC20(_token).approve(_contract, _amount)
    VestingEscrowSimple(_contract).initialize(
        self.admin, _token, _recipient, _amount, _start_time, _end_time, _can_disable
    )

    return _contract


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
