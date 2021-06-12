import brownie


def test_only_active_receiver_can_call(charlie, stream):
    with brownie.reverts("dev: caller is not receiver"):
        stream.get_reward({"from": charlie})
