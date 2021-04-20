import brownie


def test_deposit_for(accounts, rewards_only_gauge, mock_lp_token):
    mock_lp_token.approve(rewards_only_gauge, 2 ** 256 - 1, {"from": accounts[0]})
    balance = mock_lp_token.balanceOf(accounts[0])
    rewards_only_gauge.set_approve_deposit(accounts[0], True, {"from": accounts[1]})
    rewards_only_gauge.deposit(100000, accounts[1], {"from": accounts[0]})

    assert mock_lp_token.balanceOf(rewards_only_gauge) == 100000
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000
    assert rewards_only_gauge.totalSupply() == 100000
    assert rewards_only_gauge.balanceOf(accounts[1]) == 100000


def test_set_approve_deposit_initial(accounts, rewards_only_gauge):
    assert rewards_only_gauge.approved_to_deposit(accounts[0], accounts[1]) is False


def test_set_approve_deposit_true(accounts, rewards_only_gauge):
    rewards_only_gauge.set_approve_deposit(accounts[0], True, {"from": accounts[1]})
    assert rewards_only_gauge.approved_to_deposit(accounts[0], accounts[1]) is True


def test_set_approve_deposit_false(accounts, rewards_only_gauge):
    rewards_only_gauge.set_approve_deposit(accounts[0], False, {"from": accounts[1]})
    assert rewards_only_gauge.approved_to_deposit(accounts[0], accounts[1]) is False


def test_set_approve_deposit_toggle(accounts, rewards_only_gauge):
    for value in [True, True, False, False, True, False, True]:
        rewards_only_gauge.set_approve_deposit(accounts[0], value, {"from": accounts[1]})
        assert rewards_only_gauge.approved_to_deposit(accounts[0], accounts[1]) is value


def test_not_approved(accounts, rewards_only_gauge, mock_lp_token):
    mock_lp_token.approve(rewards_only_gauge, 2 ** 256 - 1, {"from": accounts[0]})
    with brownie.reverts("Not approved"):
        rewards_only_gauge.deposit(100000, accounts[1], {"from": accounts[0]})
