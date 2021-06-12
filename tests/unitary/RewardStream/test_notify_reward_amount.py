import brownie
from brownie import chain


def test_only_distributor_allowed(alice, stream):
    with brownie.reverts("dev: only distributor"):
        stream.notify_reward_amount(10 ** 18, {"from": alice})


def test_retrieves_reward_token(bob, stream, reward_token):
    stream.notify_reward_amount(10 ** 18, {"from": bob})
    post_notify = reward_token.balanceOf(stream)

    assert post_notify == 10 ** 18


def test_reward_rate_updates(bob, stream):
    stream.notify_reward_amount(10 ** 18, {"from": bob})
    post_notify = stream.reward_rate()

    assert post_notify > 0
    assert post_notify == 10 ** 18 / (86400 * 10)


def test_reward_rate_updates_mid_duration(bob, stream):
    stream.notify_reward_amount(10 ** 18, {"from": bob})
    chain.sleep(86400 * 5)  # half of the duration

    # top up the balance to be 10 ** 18 again
    stream.notify_reward_amount(10 ** 18 / 2, {"from": bob})
    post_notify = stream.reward_rate()

    assert post_notify == 10 ** 18 / (86400 * 10)


def test_period_finish_updates(bob, stream):
    tx = stream.notify_reward_amount(10 ** 18, {"from": bob})

    assert stream.period_finish() == tx.timestamp + 86400 * 10


def test_update_last_update_time(bob, stream):
    tx = stream.notify_reward_amount(10 ** 18, {"from": bob})

    assert stream.last_update_time() == tx.timestamp
