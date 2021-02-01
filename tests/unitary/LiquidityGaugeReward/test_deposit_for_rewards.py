import brownie


def test_deposit_for(accounts, liquidity_gauge_reward, mock_lp_token, reward_contract):
    mock_lp_token.approve(liquidity_gauge_reward, 2 ** 256 - 1, {"from": accounts[0]})
    balance = mock_lp_token.balanceOf(accounts[0])
    liquidity_gauge_reward.set_approve_deposit(accounts[0], True, {"from": accounts[1]})
    liquidity_gauge_reward.deposit(100000, accounts[1], {"from": accounts[0]})

    assert mock_lp_token.balanceOf(reward_contract) == 100000
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000
    assert liquidity_gauge_reward.totalSupply() == 100000
    assert liquidity_gauge_reward.balanceOf(accounts[1]) == 100000


def test_set_approve_deposit_initial(accounts, liquidity_gauge_reward):
    assert liquidity_gauge_reward.approved_to_deposit(accounts[0], accounts[1]) is False


def test_set_approve_deposit_true(accounts, liquidity_gauge_reward):
    liquidity_gauge_reward.set_approve_deposit(accounts[0], True, {"from": accounts[1]})
    assert liquidity_gauge_reward.approved_to_deposit(accounts[0], accounts[1]) is True


def test_set_approve_deposit_false(accounts, liquidity_gauge_reward):
    liquidity_gauge_reward.set_approve_deposit(accounts[0], False, {"from": accounts[1]})
    assert liquidity_gauge_reward.approved_to_deposit(accounts[0], accounts[1]) is False


def test_set_approve_deposit_toggle(accounts, liquidity_gauge_reward):
    for value in [True, True, False, False, True, False, True]:
        liquidity_gauge_reward.set_approve_deposit(accounts[0], value, {"from": accounts[1]})
        assert liquidity_gauge_reward.approved_to_deposit(accounts[0], accounts[1]) is value


def test_not_approved(accounts, liquidity_gauge_reward, mock_lp_token):
    mock_lp_token.approve(liquidity_gauge_reward, 2 ** 256 - 1, {"from": accounts[0]})
    with brownie.reverts("Not approved"):
        liquidity_gauge_reward.deposit(100000, accounts[1], {"from": accounts[0]})
