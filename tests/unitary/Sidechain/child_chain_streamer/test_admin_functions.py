import brownie


def test_set_reward_duration_admin_only(alice, bob, token, child_chain_streamer):
    with brownie.reverts("dev: only owner"):
        child_chain_streamer.set_reward_duration(token, 86400 * 7, {"from": bob})

    child_chain_streamer.set_reward_duration(token, 86400 * 7, {"from": alice})

    assert child_chain_streamer.reward_data(token)["duration"] == 86400 * 7


def test_set_reward_distributor_admin_only(alice, bob, charlie, token, child_chain_streamer):
    with brownie.reverts("dev: only owner"):
        child_chain_streamer.set_reward_distributor(token, bob, {"from": bob})

    child_chain_streamer.set_reward_distributor(token, charlie, {"from": alice})

    assert child_chain_streamer.reward_data(token)["distributor"] == charlie


def test_commit_transfer_ownership_admin_only(alice, bob, charlie, child_chain_streamer):
    with brownie.reverts("dev: only owner"):
        child_chain_streamer.commit_transfer_ownership(bob, {"from": bob})

    child_chain_streamer.commit_transfer_ownership(charlie, {"from": alice})

    assert child_chain_streamer.future_owner() == charlie


def test_accept_transfer_ownership_future_admin_only(alice, bob, charlie, child_chain_streamer):
    child_chain_streamer.commit_transfer_ownership(charlie, {"from": alice})

    with brownie.reverts("dev: only new owner"):
        child_chain_streamer.accept_transfer_ownership({"from": bob})

    child_chain_streamer.accept_transfer_ownership({"from": charlie})

    assert child_chain_streamer.owner() == charlie


def test_set_receiver_admin_only(alice, bob, charlie, child_chain_streamer):
    with brownie.reverts("dev: only owner"):
        child_chain_streamer.set_receiver(bob, {"from": bob})

    child_chain_streamer.set_receiver(charlie, {"from": alice})
    assert child_chain_streamer.reward_receiver() == charlie
