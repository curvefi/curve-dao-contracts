from collections import defaultdict

import brownie
from brownie import RewardStream, chain
from brownie.test import strategy
from brownie_tokens import ERC20

DAY = 60 * 60 * 24


class _State:
    """RewardStream.vy encapsulated state."""

    def __init__(self, owner: str, distributor: str, duration: int) -> None:
        # public getters in contract
        self.owner = owner
        self.distributor = distributor

        # time when reward distribtuion period finishes
        self.period_finish = 0
        # rate at which the reward is distributed (per block)
        self.reward_rate = 0
        # duration of the reward period (in seconds)
        self.reward_duration = duration
        # epoch time of last state changing update
        self.last_update_time = 0
        # the total amount of rewards a receiver is to receive
        self.reward_per_receiver_total = 0
        # total number of receivers
        self.receiver_count = 0
        # whether a receiver is approved to get rewards
        self.reward_receivers = defaultdict(bool)

        # private storage in contract
        # how much reward tokens a receiver has been sent
        self._reward_paid = defaultdict(int)
        self._reward_start = defaultdict(int)
        self._lifetime_earnings = defaultdict(int)

    def _update_per_receiver_total(self, timestamp: int) -> int:
        """Globally update the total amount received per receiver.

        This function updates the `self.reward_per_receiver_total` variable in the 4
        external function calls `add_receiver`, `remove_receiver`, `get_reward`,
        and `notify_reward_amount`.

        Note:
            For users that get added mid-distribution period, this function will
            set their `reward_paid` variable to the current `reward_per_receiver_total`,
            and then update the global `reward_per_receiver_total` var. This effectively
            makes it so rewards are distributed equally from the point onwards which a
            user is added.
        """
        total = self.reward_per_receiver_total
        count = self.receiver_count
        if count == 0:
            return total

        last_time = min(timestamp, self.period_finish)
        total += (last_time - self.last_update_time) * self.reward_rate // count
        self.reward_per_receiver_total = total
        self.last_update_time = last_time

        return total

    def add_receiver(self, receiver: str, msg_sender: str, timestamp: int):
        """Add a new receiver."""
        assert msg_sender == self.owner, "dev: only owner"
        assert self.reward_receivers[receiver] is False, "dev: receiver is active"

        total = self._update_per_receiver_total(timestamp)
        self.reward_receivers[receiver] = True
        self.receiver_count += 1
        self._reward_paid[receiver] = total
        self._reward_start[receiver] = total

    def remove_receiver(self, receiver: str, msg_sender: str, timestamp: int):
        """Remove a receiver, pay out their reward"""
        assert msg_sender == self.owner, "dev: only owner"
        assert self.reward_receivers[receiver] is True, "dev: receiver is inactive"

        total = self._update_per_receiver_total(timestamp)
        self.reward_receivers[receiver] = False
        self.receiver_count -= 1
        amount = total - self._reward_paid[receiver]
        if amount > 0:
            # send ERC20 reward token to `msg_sender`
            self._lifetime_earnings[receiver] += amount
        self._reward_paid[receiver] = 0
        self._reward_start[receiver] = 0

    def get_reward(self, msg_sender: str, timestamp: int):
        """Get rewards if any are available"""
        assert self.reward_receivers[msg_sender] is True, "dev: caller is not receiver"

        total = self._update_per_receiver_total(timestamp)
        amount = total - self._reward_paid[msg_sender]
        if amount > 0:
            # transfer `amount` of ERC20 tokens to `msg_sender`
            # update the total amount paid out to `msg_sender`
            self._reward_paid[msg_sender] = total
            self._lifetime_earnings[msg_sender] += amount

    def notify_reward_amount(self, amount: int, timestamp: int, msg_sender: str):
        """Add rewards to the contract for distribution."""
        assert msg_sender == self.distributor, "dev: only distributor"

        self._update_per_receiver_total(timestamp)
        if timestamp >= self.period_finish:
            # the reward distribution period has passed
            self.reward_rate = amount // self.reward_duration
        else:
            # reward distribution period currently in progress
            remaining_rewards = (self.period_finish - timestamp) * self.reward_rate
            self.reward_rate = (amount + remaining_rewards) // self.reward_duration

        self.last_update_time = timestamp
        # extend our reward duration period
        self.period_finish = timestamp + self.reward_duration

    def set_reward_duration(self, duration: int, timestamp: int, msg_sender: str):
        """Adjust the reward distribution duration."""
        assert msg_sender == self.owner, "dev: only owner"
        assert timestamp > self.period_finish, "dev: reward period currently active"

        self.reward_duration = duration


class StateMachine:

    st_uint = strategy("uint64")
    st_receiver = strategy("address")

    def __init__(cls, accounts, owner, distributor, duration, reward_token, reward_stream):
        cls.accounts = accounts
        cls.owner = str(owner)
        cls.distributor = str(distributor)
        cls.duration = duration
        cls.reward_token = reward_token
        cls.reward_stream = reward_stream

    def setup(self):
        self.state = _State(self.owner, self.distributor, self.duration)

    def initialize_rewards(self, amount="st_uint"):
        distributor_balance = self.reward_token.balanceOf(self.distributor)
        if not distributor_balance >= amount:
            self.reward_token._mint_for_testing(self.distributor, amount - distributor_balance)
        self.reward_token.approve(self.reward_stream, amount, {"from": self.distributor})

        tx = self.reward_stream.notify_reward_amount(amount, {"from": self.distributor})
        self.state.notify_reward_amount(amount, tx.timestamp, self.distributor)

    def rule_add_receiver(self, st_receiver):
        st_receiver = str(st_receiver)
        # fail route
        if self.state.reward_receivers[st_receiver] is True:
            with brownie.reverts("dev: receiver is active"):
                self.reward_stream.add_receiver(st_receiver, {"from": self.owner})
            return
        elif st_receiver == self.distributor:
            return

        # success route
        tx = self.reward_stream.add_receiver(st_receiver, {"from": self.owner})
        self.state.add_receiver(st_receiver, self.owner, tx.timestamp)

    def rule_remove_receiver(self, st_receiver):
        st_receiver = str(st_receiver)
        # fail route
        if self.state.reward_receivers[st_receiver] is False:
            with brownie.reverts("dev: receiver is inactive"):
                self.reward_stream.remove_receiver(st_receiver, {"from": self.owner})
            return

        # success route
        tx = self.reward_stream.remove_receiver(st_receiver, {"from": self.owner})
        self.state.remove_receiver(st_receiver, self.owner, tx.timestamp)

    def rule_get_reward(self, caller="st_receiver"):
        caller = str(caller)
        if self.state.reward_receivers[caller] is False:
            with brownie.reverts("dev: caller is not receiver"):
                self.reward_stream.get_reward({"from": caller})
            return

        tx = self.reward_stream.get_reward({"from": caller})
        self.state.get_reward(caller, tx.timestamp)

    def rule_notify_reward_amount(self, amount="st_uint"):
        distributor_balance = self.reward_token.balanceOf(self.distributor)
        if not distributor_balance >= amount:
            self.reward_token._mint_for_testing(self.distributor, amount - distributor_balance)
        self.reward_token.approve(self.reward_stream, amount, {"from": self.distributor})

        tx = self.reward_stream.notify_reward_amount(amount, {"from": self.distributor})
        self.state.notify_reward_amount(amount, tx.timestamp, self.distributor)

    def rule_set_reward_duration(self, duration="st_uint"):
        if chain.time() < self.state.period_finish:
            with brownie.reverts("dev: reward period currently active"):
                self.reward_stream.set_reward_duration(duration, {"from": self.owner})
            return

        tx = self.reward_stream.set_reward_duration(duration, {"from": self.owner})
        self.state.set_reward_duration(duration, tx.timestamp, self.owner)

    def invariant_sleep(self):
        chain.sleep(10)

    def invariant_state_getters(self):
        assert self.reward_stream.period_finish() == self.state.period_finish

        # invariant_reward_rate
        assert self.reward_stream.reward_rate() == self.state.reward_rate

        # invariant_reward_duration
        assert self.reward_stream.reward_duration() == self.state.reward_duration

        # invariant_last_update_time
        assert self.reward_stream.last_update_time() == self.state.last_update_time

        # invariant_reward_per_receiver_total
        assert (
            self.reward_stream.reward_per_receiver_total() == self.state.reward_per_receiver_total
        )

        # invariant_receiver_count
        assert self.reward_stream.receiver_count() == self.state.receiver_count

        # invariant_reward_receivers
        for acct, val in self.state.reward_receivers.items():
            assert self.reward_stream.reward_receivers(acct) is val

    def teardown(self):
        chain.sleep(self.state.reward_duration)

        for acct in self.state._lifetime_earnings.keys():
            if self.state.reward_receivers[acct] is True:
                tx = self.reward_stream.get_reward({"from": acct})
                self.state.get_reward(acct, tx.timestamp)
            assert self.reward_token.balanceOf(acct) == self.state._lifetime_earnings[acct]


def test_state_machine(state_machine, accounts):
    # setup
    owner = accounts[0]
    distributor = accounts[1]
    duration = DAY * 10

    # deploy reward token, and mint
    reward_token = ERC20()

    # deploy stream and approve
    reward_stream = owner.deploy(RewardStream, owner, distributor, reward_token, duration)

    # settings = {"stateful_step_count": 25}

    state_machine(
        StateMachine,
        accounts,
        owner,
        distributor,
        duration,
        reward_token,
        reward_stream,
        # settings=settings,
    )
