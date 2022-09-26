# @version 0.3.1
"""
@title Reward Forwarder
"""
from vyper.interfaces import ERC20


interface Gauge:
    def deposit_reward_token(_reward_token: address, _amount: uint256): nonpayable


GAUGE: immutable(address)


@external
def __init__(_gauge: address):
    GAUGE = _gauge


@external
def deposit_reward_token(_reward_token: address):
    """
    @param _reward_token The address of token that gets forwarded to the gauge
    @notice Deposit a reward token in the gauge
    @dev This contract should be set as the distributor of `_reward_token` in the
        gauge, else the tx will fail.
    @dev Any user can forward deposited reward tokens to a gauge, after calling
        `allow`.
    """
    Gauge(GAUGE).deposit_reward_token(_reward_token, ERC20(_reward_token).balanceOf(self))


@external
def allow(_reward_token: address):
    """
    @param _reward_token The address of token that gets forwarded to the gauge
    @notice Allow `_reward_token` to be transferred from self to Gauge
    @dev This method is a more gas efficient way to handle token approvals, by avoiding
        a storage variable to verify it token was approved, and calls to the token to
        check for approval.
    """
    response: Bytes[32] = raw_call(
        _reward_token,
        _abi_encode(GAUGE, MAX_UINT256, method_id=method_id("approve(address,uint256)")),
        max_outsize=32,
    )
    if len(response) != 0:
        assert convert(response, bool)


@pure
@external
def gauge() -> address:
    return GAUGE
