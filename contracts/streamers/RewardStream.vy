# @version 0.2.12
"""
@title RewardStream
@author Curve.Fi
@license MIT
@notice Evenly streams a reward token to one or more
        recipients over a predefined period
"""

from vyper.interfaces import ERC20

owner: public(address)
future_owner: public(address)
distributor: public(address)

reward_token: public(address)
period_finish: public(uint256)
reward_rate: public(uint256)
reward_duration: public(uint256)
last_update_time: public(uint256)
reward_per_receiver_total: public(uint256)
receiver_count: public(uint256)

reward_receivers: public(HashMap[address, bool])
reward_paid: HashMap[address, uint256]


@external
def __init__(_owner: address, _distributor: address, _token: address, _duration: uint256):
    self.owner = _owner
    self.distributor = _distributor
    self.reward_token = _token
    self.reward_duration = _duration


@internal
def _update_per_receiver_total() -> uint256:
    # update the total reward amount paid per receiver
    total: uint256 = self.reward_per_receiver_total
    count: uint256 = self.receiver_count
    if count == 0:
        return total

    last_time: uint256 = min(block.timestamp, self.period_finish)
    total += (last_time - self.last_update_time) * self.reward_rate / count
    self.reward_per_receiver_total = total
    self.last_update_time = last_time

    return total


@external
def add_receiver(_receiver: address):
    """
    @notice Add a new reward receiver
    @dev Rewards are distributed evenly between the receivers. Adding a new
         receiver does not affect the available amount of unclaimed rewards
         for other receivers.
    @param _receiver Address of the new reward receiver
    """
    assert msg.sender == self.owner  # dev: only owner
    assert not self.reward_receivers[_receiver]  # dev: receiver is active
    total: uint256 = self._update_per_receiver_total()

    self.reward_receivers[_receiver] = True
    self.receiver_count += 1
    self.reward_paid[_receiver] = total


@external
def remove_receiver(_receiver: address):
    """
    @notice Remove an existing reward receiver
    @dev Removing a receiver distributes any unclaimed rewards to that receiver.
    @param _receiver Address of the reward receiver being removed
    """
    assert msg.sender == self.owner  # dev: only owner
    assert self.reward_receivers[_receiver]  # dev: receiver is inactive
    total: uint256 = self._update_per_receiver_total()

    self.reward_receivers[_receiver] = False
    self.receiver_count -= 1
    amount: uint256 = total - self.reward_paid[_receiver]
    if amount > 0:
        assert ERC20(self.reward_token).transfer(_receiver, amount)  # dev: invalid response
    self.reward_paid[_receiver] = 0


@external
def get_reward():
    """
    @notice Claim pending rewards
    """
    assert self.reward_receivers[msg.sender]  # dev: caller is not receiver
    total: uint256 = self._update_per_receiver_total()
    amount: uint256 = total - self.reward_paid[msg.sender]
    if amount > 0:
        assert ERC20(self.reward_token).transfer(msg.sender, amount)  # dev: invalid response
        self.reward_paid[msg.sender] = total


@external
def notify_reward_amount(_amount: uint256):
    """
    @notice Transfer new reward tokens into the contract
    @dev Only callable by the distributor. Reward tokens are distributed
         evenly between receivers, over `reward_duration` seconds.
    @param _amount Amount of reward tokens to add
    """
    assert msg.sender == self.distributor  # dev: only distributor
    self._update_per_receiver_total()
    assert ERC20(self.reward_token).transferFrom(msg.sender, self, _amount)  # dev: invalid response
    duration: uint256 = self.reward_duration
    if block.timestamp >= self.period_finish:
        self.reward_rate = _amount / duration
    else:
        remaining: uint256 = self.period_finish - block.timestamp
        leftover: uint256 = remaining * self.reward_rate
        self.reward_rate = (_amount + leftover) / duration

    self.last_update_time = block.timestamp
    self.period_finish = block.timestamp + duration


@external
def set_reward_duration(_duration: uint256):
    """
    @notice Modify the duration that rewards are distributed over
    @dev Only callable when there is not an active reward period
    @param _duration Number of seconds to distribute rewards over
    """
    assert msg.sender == self.owner  # dev: only owner
    assert block.timestamp > self.period_finish  # dev: reward period currently active
    self.reward_duration = _duration


@external
def set_reward_distributor(_distributor: address):
    """
    @notice Modify the reward distributor
    @param _distributor Reward distributor
    """
    assert msg.sender == self.owner  # dev: only owner
    self.distributor = _distributor


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
