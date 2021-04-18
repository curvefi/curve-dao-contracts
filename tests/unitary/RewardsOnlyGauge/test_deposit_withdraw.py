import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def deposit_setup(accounts, rewards_only_gauge, mock_lp_token):
    mock_lp_token.approve(rewards_only_gauge, 2 ** 256 - 1, {"from": accounts[0]})


def test_deposit(accounts, rewards_only_gauge, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])
    rewards_only_gauge.deposit(100000, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(rewards_only_gauge) == 100000
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000
    assert rewards_only_gauge.totalSupply() == 100000
    assert rewards_only_gauge.balanceOf(accounts[0]) == 100000


def test_deposit_zero(accounts, rewards_only_gauge, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])
    rewards_only_gauge.deposit(0, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(rewards_only_gauge) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance
    assert rewards_only_gauge.totalSupply() == 0
    assert rewards_only_gauge.balanceOf(accounts[0]) == 0


def test_deposit_insufficient_balance(accounts, rewards_only_gauge, mock_lp_token):
    with brownie.reverts():
        rewards_only_gauge.deposit(100000, {"from": accounts[1]})


def test_withdraw(accounts, rewards_only_gauge, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])

    rewards_only_gauge.deposit(100000, {"from": accounts[0]})
    rewards_only_gauge.withdraw(100000, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(rewards_only_gauge) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance
    assert rewards_only_gauge.totalSupply() == 0
    assert rewards_only_gauge.balanceOf(accounts[0]) == 0


def test_withdraw_zero(accounts, rewards_only_gauge, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])
    rewards_only_gauge.deposit(100000, {"from": accounts[0]})
    rewards_only_gauge.withdraw(0, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(rewards_only_gauge) == 100000
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000
    assert rewards_only_gauge.totalSupply() == 100000
    assert rewards_only_gauge.balanceOf(accounts[0]) == 100000


def test_withdraw_new_epoch(accounts, chain, rewards_only_gauge, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])

    rewards_only_gauge.deposit(100000, {"from": accounts[0]})
    chain.sleep(86400 * 400)
    rewards_only_gauge.withdraw(100000, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(rewards_only_gauge) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance
    assert rewards_only_gauge.totalSupply() == 0
    assert rewards_only_gauge.balanceOf(accounts[0]) == 0
