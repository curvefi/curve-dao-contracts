import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def deposit_setup(accounts, liquidity_gauge_reward, mock_lp_token):
    mock_lp_token.approve(liquidity_gauge_reward, 2 ** 256 - 1, {"from": accounts[0]})


def test_deposit(accounts, liquidity_gauge_reward, mock_lp_token, reward_contract):
    balance = mock_lp_token.balanceOf(accounts[0])
    liquidity_gauge_reward.deposit(100000, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(reward_contract) == 100000
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000
    assert liquidity_gauge_reward.totalSupply() == 100000
    assert liquidity_gauge_reward.balanceOf(accounts[0]) == 100000


def test_deposit_zero(accounts, liquidity_gauge_reward, mock_lp_token, reward_contract):
    balance = mock_lp_token.balanceOf(accounts[0])
    liquidity_gauge_reward.deposit(0, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(reward_contract) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance
    assert liquidity_gauge_reward.totalSupply() == 0
    assert liquidity_gauge_reward.balanceOf(accounts[0]) == 0


def test_deposit_insufficient_balance(accounts, liquidity_gauge_reward, mock_lp_token):
    with brownie.reverts():
        liquidity_gauge_reward.deposit(100000, {"from": accounts[1]})


def test_withdraw(accounts, liquidity_gauge_reward, mock_lp_token, reward_contract):
    balance = mock_lp_token.balanceOf(accounts[0])

    liquidity_gauge_reward.deposit(100000, {"from": accounts[0]})
    liquidity_gauge_reward.withdraw(100000, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(reward_contract) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance
    assert liquidity_gauge_reward.totalSupply() == 0
    assert liquidity_gauge_reward.balanceOf(accounts[0]) == 0


def test_withdraw_zero(accounts, liquidity_gauge_reward, mock_lp_token, reward_contract):
    balance = mock_lp_token.balanceOf(accounts[0])
    liquidity_gauge_reward.deposit(100000, {"from": accounts[0]})
    liquidity_gauge_reward.withdraw(0, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(reward_contract) == 100000
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000
    assert liquidity_gauge_reward.totalSupply() == 100000
    assert liquidity_gauge_reward.balanceOf(accounts[0]) == 100000


def test_withdraw_new_epoch(
    accounts, chain, liquidity_gauge_reward, mock_lp_token, reward_contract
):
    balance = mock_lp_token.balanceOf(accounts[0])

    liquidity_gauge_reward.deposit(100000, {"from": accounts[0]})
    chain.sleep(86400 * 400)
    liquidity_gauge_reward.withdraw(100000, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(reward_contract) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance
    assert liquidity_gauge_reward.totalSupply() == 0
    assert liquidity_gauge_reward.balanceOf(accounts[0]) == 0
