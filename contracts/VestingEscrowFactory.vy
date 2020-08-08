# @version 0.2.4
"""
@title Vesting Escrow Factory
@notice Stores and distributes `ERC20CRV` tokens by deploying `VestingEscrowSimple` contracts
"""

from vyper.interfaces import ERC20

MIN_VESTING_START: constant(uint256) = 86400 * 365


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
    """
    @notice Contract constructor
    @dev Prior to deployment you must deploy one copy of `VestingEscrowSimple` which
         is used as a library for vesting contracts deployed by this factory
    @param _target `VestingEscrowSimple` contract address
    """
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
    """
    @notice Deploy a new vesting contract
    @dev Each contract holds tokens which vest for a single account. Tokens
         must be sent to this contract via the regular `ERC20.transfer` method
         prior to calling this method.
    @param _token Address of the ERC20 token being distributed
    @param _recipient Address to vest tokens for
    @param _amount Amount of tokens being vested for `_recipient`
    @param _start_time Epoch time at which token distribution starts
    @param _end_time Time until everything should be vested
    @param _can_disable Can admin disable recipient's ability to claim tokens?
    """
    assert msg.sender == self.admin  # dev: admin only
    assert _start_time >= block.timestamp + MIN_VESTING_START  # dev: start time too soon
    assert _end_time > _start_time  # dev: end before start

    _contract: address = create_forwarder_to(self.target)
    assert ERC20(_token).approve(_contract, _amount)  # dev: approve failed
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
    assert _admin != ZERO_ADDRESS  # dev: admin not set
    self.admin = _admin
    log ApplyOwnership(_admin)

    return True
