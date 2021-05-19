import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(
    accounts,
    gauge_controller,
    minter,
    liquidity_gauge_reward,
    reward_gauge_wrapper,
    token,
    mock_lp_token,
):
    token.set_minter(minter, {"from": accounts[0]})

    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": accounts[0]})
    gauge_controller.add_gauge(liquidity_gauge_reward, 0, 0, {"from": accounts[0]})

    mock_lp_token.approve(reward_gauge_wrapper, 2 ** 256 - 1, {"from": accounts[0]})


def test_deposit(
    accounts, liquidity_gauge_reward, reward_gauge_wrapper, reward_contract, mock_lp_token,
):
    balance = mock_lp_token.balanceOf(accounts[0])
    reward_gauge_wrapper.deposit(100000, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(reward_contract) == 100000
    assert mock_lp_token.balanceOf(reward_gauge_wrapper) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000

    assert liquidity_gauge_reward.totalSupply() == 100000
    assert liquidity_gauge_reward.balanceOf(reward_gauge_wrapper) == 100000

    assert reward_gauge_wrapper.totalSupply() == 100000
    assert reward_gauge_wrapper.balanceOf(accounts[0]) == 100000


def test_deposit_zero(
    accounts, liquidity_gauge_reward, reward_gauge_wrapper, reward_contract, mock_lp_token,
):
    balance = mock_lp_token.balanceOf(accounts[0])
    liquidity_gauge_reward.deposit(0, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(reward_contract) == 0
    assert mock_lp_token.balanceOf(reward_gauge_wrapper) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance

    assert liquidity_gauge_reward.totalSupply() == 0
    assert liquidity_gauge_reward.balanceOf(reward_gauge_wrapper) == 0

    assert reward_gauge_wrapper.totalSupply() == 0
    assert reward_gauge_wrapper.balanceOf(accounts[0]) == 0


def test_deposit_insufficient_balance(accounts, reward_gauge_wrapper):
    with brownie.reverts():
        reward_gauge_wrapper.deposit(100000, {"from": accounts[1]})


def test_withdraw(
    accounts, liquidity_gauge_reward, reward_gauge_wrapper, reward_contract, mock_lp_token,
):
    balance = mock_lp_token.balanceOf(accounts[0])

    reward_gauge_wrapper.deposit(100000, {"from": accounts[0]})
    reward_gauge_wrapper.withdraw(100000, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(reward_contract) == 0
    assert mock_lp_token.balanceOf(reward_gauge_wrapper) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance

    assert liquidity_gauge_reward.totalSupply() == 0
    assert liquidity_gauge_reward.balanceOf(reward_gauge_wrapper) == 0

    assert reward_gauge_wrapper.totalSupply() == 0
    assert reward_gauge_wrapper.balanceOf(accounts[0]) == 0


def test_withdraw_zero(
    accounts, liquidity_gauge_reward, reward_gauge_wrapper, reward_contract, mock_lp_token,
):
    balance = mock_lp_token.balanceOf(accounts[0])
    reward_gauge_wrapper.deposit(100000, {"from": accounts[0]})
    reward_gauge_wrapper.withdraw(0, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(reward_contract) == 100000
    assert mock_lp_token.balanceOf(reward_gauge_wrapper) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000

    assert liquidity_gauge_reward.totalSupply() == 100000
    assert liquidity_gauge_reward.balanceOf(reward_gauge_wrapper) == 100000

    assert reward_gauge_wrapper.totalSupply() == 100000
    assert reward_gauge_wrapper.balanceOf(accounts[0]) == 100000


def test_withdraw_new_epoch(
    accounts, chain, liquidity_gauge_reward, reward_gauge_wrapper, reward_contract, mock_lp_token,
):
    balance = mock_lp_token.balanceOf(accounts[0])

    reward_gauge_wrapper.deposit(100000, {"from": accounts[0]})
    chain.sleep(86400 * 400)
    reward_gauge_wrapper.withdraw(100000, {"from": accounts[0]})

    assert mock_lp_token.balanceOf(reward_contract) == 0
    assert mock_lp_token.balanceOf(reward_gauge_wrapper) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance

    assert liquidity_gauge_reward.totalSupply() == 0
    assert liquidity_gauge_reward.balanceOf(reward_gauge_wrapper) == 0

    assert reward_gauge_wrapper.totalSupply() == 0
    assert reward_gauge_wrapper.balanceOf(accounts[0]) == 0


def test_transfer_and_withdraw(accounts, reward_gauge_wrapper, mock_lp_token):

    reward_gauge_wrapper.deposit(100000, {"from": accounts[0]})
    reward_gauge_wrapper.transfer(accounts[1], 100000)
    reward_gauge_wrapper.withdraw(100000, {"from": accounts[1]})

    assert mock_lp_token.balanceOf(accounts[1]) == 100000


def test_cannot_withdraw_after_transfer(accounts, reward_gauge_wrapper, mock_lp_token):

    reward_gauge_wrapper.deposit(100000, {"from": accounts[0]})
    reward_gauge_wrapper.transfer(accounts[1], 100000)

    with brownie.reverts():
        reward_gauge_wrapper.withdraw(100000, {"from": accounts[0]})
