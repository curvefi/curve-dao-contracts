import brownie


def test_deposit_for(accounts, liquidity_gauge, mock_lp_token):
    mock_lp_token.approve(liquidity_gauge, 2 ** 256 - 1, {"from": accounts[0]})
    balance = mock_lp_token.balanceOf(accounts[0])
    liquidity_gauge.set_approve_deposit(accounts[0], True, {"from": accounts[1]})
    liquidity_gauge.deposit(100000, accounts[1], {"from": accounts[0]})

    assert mock_lp_token.balanceOf(liquidity_gauge) == 100000
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000
    assert liquidity_gauge.totalSupply() == 100000
    assert liquidity_gauge.balanceOf(accounts[1]) == 100000


def test_set_approve_deposit_initial(accounts, liquidity_gauge):
    assert liquidity_gauge.approved_to_deposit(accounts[0], accounts[1]) is False


def test_set_approve_deposit_true(accounts, liquidity_gauge):
    liquidity_gauge.set_approve_deposit(accounts[0], True, {"from": accounts[1]})
    assert liquidity_gauge.approved_to_deposit(accounts[0], accounts[1]) is True


def test_set_approve_deposit_false(accounts, liquidity_gauge):
    liquidity_gauge.set_approve_deposit(accounts[0], False, {"from": accounts[1]})
    assert liquidity_gauge.approved_to_deposit(accounts[0], accounts[1]) is False


def test_set_approve_deposit_toggle(accounts, liquidity_gauge):
    for value in [True, True, False, False, True, False, True]:
        liquidity_gauge.set_approve_deposit(accounts[0], value, {"from": accounts[1]})
        assert liquidity_gauge.approved_to_deposit(accounts[0], accounts[1]) is value


def test_not_approved(accounts, liquidity_gauge, mock_lp_token):
    mock_lp_token.approve(liquidity_gauge, 2 ** 256 - 1, {"from": accounts[0]})
    with brownie.reverts("Not approved"):
        liquidity_gauge.deposit(100000, accounts[1], {"from": accounts[0]})
