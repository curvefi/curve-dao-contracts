import brownie


def test_updates_reward_duration(alice, stream):
    pre_update = stream.reward_duration()
    stream.set_reward_duration(86400 * 365, {"from": alice})

    assert pre_update == 86400 * 10
    assert stream.reward_duration() == 86400 * 365


def test_only_owner(charlie, stream):
    with brownie.reverts("dev: only owner"):
        stream.set_reward_duration(10, {"from": charlie})


def test_mid_reward_distribution_period(alice, bob, stream):
    stream.notify_reward_amount(10 ** 18, {"from": bob})

    with brownie.reverts("dev: reward period currently active"):
        stream.set_reward_duration(10, {"from": alice})
