import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def deposit_setup(accounts, gauge_v2, mock_lp_token):
    mock_lp_token.approve(gauge_v2, 2 ** 256 - 1, {"from": accounts[0]})


def test_deposit(accounts, gauge_v2, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])
    gauge_v2.deposit(100000, {'from': accounts[0]})

    assert mock_lp_token.balanceOf(gauge_v2) == 100000
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000
    assert gauge_v2.totalSupply() == 100000
    assert gauge_v2.balanceOf(accounts[0]) == 100000


def test_deposit_zero(accounts, gauge_v2, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])
    gauge_v2.deposit(0, {'from': accounts[0]})

    assert mock_lp_token.balanceOf(gauge_v2) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance
    assert gauge_v2.totalSupply() == 0
    assert gauge_v2.balanceOf(accounts[0]) == 0


def test_deposit_insufficient_balance(accounts, gauge_v2, mock_lp_token):
    with brownie.reverts():
        gauge_v2.deposit(100000, {'from': accounts[1]})


def test_withdraw(accounts, gauge_v2, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])

    gauge_v2.deposit(100000, {'from': accounts[0]})
    gauge_v2.withdraw(100000, {'from': accounts[0]})

    assert mock_lp_token.balanceOf(gauge_v2) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance
    assert gauge_v2.totalSupply() == 0
    assert gauge_v2.balanceOf(accounts[0]) == 0


def test_withdraw_zero(accounts, gauge_v2, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])
    gauge_v2.deposit(100000, {'from': accounts[0]})
    gauge_v2.withdraw(0, {'from': accounts[0]})

    assert mock_lp_token.balanceOf(gauge_v2) == 100000
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000
    assert gauge_v2.totalSupply() == 100000
    assert gauge_v2.balanceOf(accounts[0]) == 100000


def test_withdraw_new_epoch(accounts, chain, gauge_v2, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])

    gauge_v2.deposit(100000, {'from': accounts[0]})
    chain.sleep(86400 * 400)
    gauge_v2.withdraw(100000, {'from': accounts[0]})

    assert mock_lp_token.balanceOf(gauge_v2) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance
    assert gauge_v2.totalSupply() == 0
    assert gauge_v2.balanceOf(accounts[0]) == 0
