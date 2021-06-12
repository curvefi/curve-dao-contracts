import brownie
import pytest
from brownie import chain


@pytest.fixture(autouse=True)
def module_setup(alice, bob, charlie, stream, reward_token):
    stream.add_receiver(charlie, {"from": alice})
    stream.notify_reward_amount(10 ** 18, {"from": bob})
    chain.sleep(86400 * 10)


def test_receiver_deactivates(alice, charlie, stream):
    pre_remove = stream.reward_receivers(charlie)
    stream.remove_receiver(charlie, {"from": alice})

    assert pre_remove is True
    assert stream.reward_receivers(charlie) is False


def test_receiver_count_decreases(alice, charlie, stream):
    pre_remove = stream.receiver_count()
    stream.remove_receiver(charlie, {"from": alice})
    post_remove = stream.receiver_count()

    assert post_remove == pre_remove - 1


def test_updates_last_update_time(alice, charlie, stream):
    pre_remove = stream.last_update_time()
    tx = stream.remove_receiver(charlie, {"from": alice})
    post_remove = stream.last_update_time()

    assert pre_remove < post_remove
    assert post_remove == tx.timestamp


def test_updates_reward_per_receiver_total(alice, charlie, stream):
    pre_remove = stream.reward_per_receiver_total()
    stream.remove_receiver(charlie, {"from": alice})
    post_remove = stream.reward_per_receiver_total()

    assert pre_remove < post_remove
    assert 0.9999 < post_remove / 10 ** 18 <= 1


def test_reverts_for_non_owner(bob, charlie, stream):
    with brownie.reverts("dev: only owner"):
        stream.remove_receiver(charlie, {"from": bob})


def test_reverts_for_inactive_receiver(alice, bob, stream):
    with brownie.reverts("dev: receiver is inactive"):
        stream.remove_receiver(bob, {"from": alice})
