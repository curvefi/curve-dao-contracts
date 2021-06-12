from brownie import chain


def test_single_receiver(stream, alice, bob, charlie, reward_token):
    stream.add_receiver(charlie, {"from": alice})
    stream.notify_reward_amount(10 ** 18, {"from": bob})
    chain.sleep(86400 * 10)

    stream.get_reward({"from": charlie})

    assert 0.9999 <= reward_token.balanceOf(charlie) / 10 ** 18 <= 1


def test_single_receiver_partial_duration(stream, alice, bob, charlie, reward_token):
    stream.add_receiver(charlie, {"from": alice})
    tx = stream.notify_reward_amount(10 ** 18, {"from": bob})
    start = tx.timestamp - 1

    for i in range(1, 10):
        chain.mine(timestamp=start + 86400 * i)
        stream.get_reward({"from": charlie})
        assert 0.9999 <= reward_token.balanceOf(charlie) / (i * 10 ** 17) <= 1


def test_multiple_receivers(stream, alice, bob, accounts, reward_token):
    for i in range(2, 6):
        stream.add_receiver(accounts[i], {"from": alice})
    tx = stream.notify_reward_amount(10 ** 18, {"from": bob})
    start = tx.timestamp - 1

    for i in range(1, 10):
        chain.mine(timestamp=start + 86400 * i)
        for x in range(2, 6):
            stream.get_reward({"from": accounts[x]})

        balances = [reward_token.balanceOf(i) for i in accounts[2:6]]
        assert 0.9999 < min(balances) / max(balances) <= 1
        assert 0.9999 <= sum(balances) / (i * 10 ** 17) <= 1


def test_add_receiver_during_period(stream, alice, bob, charlie, reward_token):
    stream.add_receiver(charlie, {"from": alice})
    stream.notify_reward_amount(10 ** 18, {"from": bob})
    chain.sleep(86400 * 5)
    stream.add_receiver(alice, {"from": alice})
    chain.sleep(86400 * 5)

    stream.get_reward({"from": alice})
    stream.get_reward({"from": charlie})
    alice_balance = reward_token.balanceOf(alice)
    charlie_balance = reward_token.balanceOf(charlie)

    assert 0.9999 <= alice_balance * 3 / charlie_balance <= 1
    assert 0.9999 <= (alice_balance + charlie_balance) / 10 ** 18 <= 1


def test_remove_receiver_during_period(stream, alice, bob, charlie, reward_token):
    stream.add_receiver(alice, {"from": alice})
    stream.add_receiver(charlie, {"from": alice})
    stream.notify_reward_amount(10 ** 18, {"from": bob})
    chain.sleep(86400 * 5)
    stream.remove_receiver(alice, {"from": alice})
    chain.sleep(86400 * 5)

    stream.get_reward({"from": charlie})
    alice_balance = reward_token.balanceOf(alice)
    charlie_balance = reward_token.balanceOf(charlie)

    assert 0.9999 <= alice_balance * 3 / charlie_balance <= 1
    assert 0.9999 <= (alice_balance + charlie_balance) / 10 ** 18 <= 1
