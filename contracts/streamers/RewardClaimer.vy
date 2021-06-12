# @version 0.2.12
"""
@title RewardClaimer
@author Curve.Fi
@license MIT
@notice Passthrough to allow claiming from multiple reward streamers
"""

from vyper.interfaces import ERC20


interface RewardStream:
    def get_reward(): nonpayable


struct RewardData:
    claim: address
    reward: address


owner: public(address)
future_owner: public(address)
reward_receiver: public(address)

reward_data: public(RewardData[4])


@external
def __init__(_owner: address, _reward_receiver: address):
    """
    @notice Contract constructor
    @param _owner Owner address
    @param _reward_receiver Reward receiver address
    """
    self.owner = _owner
    self.reward_receiver = _reward_receiver


@external
def get_reward():
    """
    @notice Claim all available rewards
    @dev Only callable by the reward receiver
    """
    assert msg.sender == self.reward_receiver

    for i in range(4):
        data: RewardData = self.reward_data[i]
        if data.reward == ZERO_ADDRESS:
            break

        RewardStream(data.claim).get_reward()
        amount: uint256 = ERC20(data.reward).balanceOf(self)
        if amount > 0:
            assert ERC20(data.reward).transfer(msg.sender, amount)


@external
def set_reward_data(_idx: uint256, _claim: address, _reward: address):
    """
    @notice Set data about a reward streamer
    @dev Only callable by the owner
    @param _idx Index of `reward_data` to modify
    @param _claim Address of the streamer to claim from
    @param _reward Address of the reward token
    """
    assert msg.sender == self.owner

    self.reward_data[_idx] = RewardData({claim: _claim, reward: _reward})


@external
def commit_transfer_ownership(_owner: address):
    """
    @notice Initiate ownership tansfer of the contract
    @param _owner Address to have ownership transferred to
    """
    assert msg.sender == self.owner  # dev: only owner

    self.future_owner = _owner


@external
def accept_transfer_ownership():
    """
    @notice Accept a pending ownership transfer
    """
    owner: address = self.future_owner
    assert msg.sender == owner  # dev: only new owner

    self.owner = owner
