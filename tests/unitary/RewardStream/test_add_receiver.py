import brownie


def test_receiver_count_increases(alice, charlie, stream):
    pre_receiver_count = stream.receiver_count()
    stream.add_receiver(charlie, {"from": alice})

    assert stream.receiver_count() == pre_receiver_count + 1


def test_receiver_activation(alice, charlie, stream):
    pre_activation = stream.reward_receivers(charlie)
    stream.add_receiver(charlie, {"from": alice})

    assert pre_activation is False
    assert stream.reward_receivers(charlie) is True


def test_reverts_for_non_owner(bob, charlie, stream):
    with brownie.reverts("dev: only owner"):
        stream.add_receiver(charlie, {"from": bob})


def test_reverts_for_active_receiver(alice, charlie, stream):
    stream.add_receiver(charlie, {"from": alice})
    with brownie.reverts("dev: receiver is active"):
        stream.add_receiver(charlie, {"from": alice})
