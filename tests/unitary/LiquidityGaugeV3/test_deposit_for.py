import brownie


def test_deposit_for(accounts, gauge_v3, mock_lp_token):
    mock_lp_token.approve(gauge_v3, 2 ** 256 - 1, {"from": accounts[0]})
    balance = mock_lp_token.balanceOf(accounts[0])
    gauge_v3.set_approve_deposit(accounts[0], True, {"from": accounts[1]})
    gauge_v3.deposit(100000, accounts[1], {"from": accounts[0]})

    assert mock_lp_token.balanceOf(gauge_v3) == 100000
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000
    assert gauge_v3.totalSupply() == 100000
    assert gauge_v3.balanceOf(accounts[1]) == 100000


def test_set_approve_deposit_initial(accounts, gauge_v3):
    assert gauge_v3.approved_to_deposit(accounts[0], accounts[1]) is False


def test_set_approve_deposit_true(accounts, gauge_v3):
    gauge_v3.set_approve_deposit(accounts[0], True, {"from": accounts[1]})
    assert gauge_v3.approved_to_deposit(accounts[0], accounts[1]) is True


def test_set_approve_deposit_false(accounts, gauge_v3):
    gauge_v3.set_approve_deposit(accounts[0], False, {"from": accounts[1]})
    assert gauge_v3.approved_to_deposit(accounts[0], accounts[1]) is False


def test_set_approve_deposit_toggle(accounts, gauge_v3):
    for value in [True, True, False, False, True, False, True]:
        gauge_v3.set_approve_deposit(accounts[0], value, {"from": accounts[1]})
        assert gauge_v3.approved_to_deposit(accounts[0], accounts[1]) is value


def test_not_approved(accounts, gauge_v3, mock_lp_token):
    mock_lp_token.approve(gauge_v3, 2 ** 256 - 1, {"from": accounts[0]})
    with brownie.reverts("Not approved"):
        gauge_v3.deposit(100000, accounts[1], {"from": accounts[0]})
