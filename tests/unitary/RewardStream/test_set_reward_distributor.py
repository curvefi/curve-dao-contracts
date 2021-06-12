import brownie


def test_successful_change(alice, charlie, stream):
    stream.set_reward_distributor(charlie, {"from": alice})

    assert stream.distributor() == charlie


def test_only_owner(bob, charlie, stream):
    with brownie.reverts("dev: only owner"):
        stream.set_reward_distributor(charlie, {"from": bob})
