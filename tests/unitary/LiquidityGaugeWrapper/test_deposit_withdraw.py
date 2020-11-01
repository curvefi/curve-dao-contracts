import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def deposit_setup(accounts, gauge_controller, minter, liquidity_gauge, gauge_wrapper, token, mock_lp_token):
    token.set_minter(minter, {'from': accounts[0]})

    gauge_controller.add_type(b'Liquidity', 10**10, {'from': accounts[0]})
    gauge_controller.add_gauge(liquidity_gauge, 0, 0, {'from': accounts[0]})

    mock_lp_token.approve(gauge_wrapper, 2 ** 256 - 1, {"from": accounts[0]})


def test_deposit(accounts, liquidity_gauge, gauge_wrapper, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])
    gauge_wrapper.deposit(100000, {'from': accounts[0]})

    assert mock_lp_token.balanceOf(liquidity_gauge) == 100000
    assert mock_lp_token.balanceOf(gauge_wrapper) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000

    assert liquidity_gauge.totalSupply() == 100000
    assert liquidity_gauge.balanceOf(gauge_wrapper) == 100000

    assert gauge_wrapper.totalSupply() == 100000
    assert gauge_wrapper.balanceOf(accounts[0]) == 100000


def test_deposit_zero(accounts, liquidity_gauge, gauge_wrapper, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])
    liquidity_gauge.deposit(0, {'from': accounts[0]})

    assert mock_lp_token.balanceOf(liquidity_gauge) == 0
    assert mock_lp_token.balanceOf(gauge_wrapper) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance

    assert liquidity_gauge.totalSupply() == 0
    assert liquidity_gauge.balanceOf(gauge_wrapper) == 0

    assert gauge_wrapper.totalSupply() == 0
    assert gauge_wrapper.balanceOf(accounts[0]) == 0


def test_deposit_insufficient_balance(accounts, gauge_wrapper):
    with brownie.reverts():
        gauge_wrapper.deposit(100000, {'from': accounts[1]})


def test_withdraw(accounts, liquidity_gauge, gauge_wrapper, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])

    gauge_wrapper.deposit(100000, {'from': accounts[0]})
    gauge_wrapper.withdraw(100000, {'from': accounts[0]})

    assert mock_lp_token.balanceOf(liquidity_gauge) == 0
    assert mock_lp_token.balanceOf(gauge_wrapper) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance

    assert liquidity_gauge.totalSupply() == 0
    assert liquidity_gauge.balanceOf(gauge_wrapper) == 0

    assert gauge_wrapper.totalSupply() == 0
    assert gauge_wrapper.balanceOf(accounts[0]) == 0


def test_withdraw_zero(accounts, liquidity_gauge, gauge_wrapper, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])
    gauge_wrapper.deposit(100000, {'from': accounts[0]})
    gauge_wrapper.withdraw(0, {'from': accounts[0]})

    assert mock_lp_token.balanceOf(liquidity_gauge) == 100000
    assert mock_lp_token.balanceOf(gauge_wrapper) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance - 100000

    assert liquidity_gauge.totalSupply() == 100000
    assert liquidity_gauge.balanceOf(gauge_wrapper) == 100000

    assert gauge_wrapper.totalSupply() == 100000
    assert gauge_wrapper.balanceOf(accounts[0]) == 100000


def test_withdraw_new_epoch(accounts, chain, liquidity_gauge, gauge_wrapper, mock_lp_token):
    balance = mock_lp_token.balanceOf(accounts[0])

    gauge_wrapper.deposit(100000, {'from': accounts[0]})
    chain.sleep(86400 * 400)
    gauge_wrapper.withdraw(100000, {'from': accounts[0]})

    assert mock_lp_token.balanceOf(liquidity_gauge) == 0
    assert mock_lp_token.balanceOf(gauge_wrapper) == 0
    assert mock_lp_token.balanceOf(accounts[0]) == balance

    assert liquidity_gauge.totalSupply() == 0
    assert liquidity_gauge.balanceOf(gauge_wrapper) == 0

    assert gauge_wrapper.totalSupply() == 0
    assert gauge_wrapper.balanceOf(accounts[0]) == 0


def test_transfer_and_withdraw(accounts, gauge_wrapper, mock_lp_token):

    gauge_wrapper.deposit(100000, {'from': accounts[0]})
    gauge_wrapper.transfer(accounts[1], 100000)
    gauge_wrapper.withdraw(100000, {'from': accounts[1]})

    assert mock_lp_token.balanceOf(accounts[1]) == 100000


def test_cannot_withdraw_after_transfer(accounts, gauge_wrapper, mock_lp_token):

    gauge_wrapper.deposit(100000, {'from': accounts[0]})
    gauge_wrapper.transfer(accounts[1], 100000)

    with brownie.reverts():
        gauge_wrapper.withdraw(100000, {'from': accounts[0]})
