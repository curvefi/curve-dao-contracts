import brownie


def test_only_owner(bob, child_chain_streamer, token):
    with brownie.reverts("dev: owner only"):
        child_chain_streamer.add_reward(token, bob, 86400 * 7, {"from": bob})


def test_reward_data_updated(alice, charlie, child_chain_streamer, token):

    child_chain_streamer.add_reward(token, charlie, 86400 * 7, {"from": alice})
    expected_data = (charlie, 0, 0, 86400 * 7, 0, 0)

    assert child_chain_streamer.reward_count() == 2
    assert child_chain_streamer.reward_tokens(1) == token
    assert child_chain_streamer.reward_data(token) == expected_data


def test_reverts_for_double_adding(alice, charlie, child_chain_streamer, token):
    child_chain_streamer.add_reward(token, charlie, 86400 * 7, {"from": alice})

    with brownie.reverts("Reward token already added"):
        child_chain_streamer.add_reward(token, charlie, 86400 * 7, {"from": alice})
