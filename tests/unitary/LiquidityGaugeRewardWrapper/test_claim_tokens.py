import brownie
import pytest
import itertools

MONTH = 86400 * 30
WEEK = 86400 * 7

@pytest.fixture(scope="module", autouse=True)
def setup(accounts, mock_lp_token, token, minter, gauge_controller, liquidity_gauge_reward, reward_gauge_wrapper, reward_contract, coin_reward):
    token.set_minter(minter, {'from': accounts[0]})

    gauge_controller.add_type(b'Liquidity', 10**10, {'from': accounts[0]})
    gauge_controller.add_gauge(liquidity_gauge_reward, 0, 10**18, {'from': accounts[0]})

    coin_reward._mint_for_testing(10**20, {'from': accounts[0]})
    coin_reward.transfer(reward_contract, 10**20, {'from': accounts[0]})
    reward_contract.notifyRewardAmount(10**20, {'from': accounts[0]})

    # transfer tokens
    for acct in accounts[1:3]:
        mock_lp_token.transfer(acct, 1e18, {'from': accounts[0]})

    # approve gauge and wrapper
    for gauge, acct in itertools.product([liquidity_gauge_reward, reward_gauge_wrapper], accounts[1:3]):
        mock_lp_token.approve(gauge, 1e18, {'from': acct})


def test_claim_crv(accounts, chain, liquidity_gauge_reward, reward_gauge_wrapper, token):
    reward_gauge_wrapper.deposit(1e18, {'from': accounts[1]})

    chain.sleep(MONTH)
    reward_gauge_wrapper.claim_tokens({'from': accounts[1]})
    expected = liquidity_gauge_reward.integrate_fraction(reward_gauge_wrapper)

    assert expected > 0
    assert token.balanceOf(accounts[1]) == expected


def test_claim_reward(accounts, chain, liquidity_gauge_reward, reward_gauge_wrapper, coin_reward):
    reward_gauge_wrapper.deposit(1e18, {'from': accounts[1]})

    chain.sleep(MONTH)
    reward_gauge_wrapper.claim_tokens({'from': accounts[1]})

    assert coin_reward.balanceOf(accounts[1]) > 0
    assert coin_reward.balanceOf(reward_gauge_wrapper) == 0


def test_multiple_depositors(accounts, chain, liquidity_gauge_reward, reward_gauge_wrapper, token):
    reward_gauge_wrapper.deposit(1e18, {'from': accounts[1]})

    chain.sleep(MONTH)
    reward_gauge_wrapper.deposit(1e18, {'from': accounts[2]})
    chain.sleep(MONTH)
    reward_gauge_wrapper.withdraw(1e18, {'from': accounts[1]})
    reward_gauge_wrapper.withdraw(1e18, {'from': accounts[2]})
    chain.sleep(10)


    reward_gauge_wrapper.claim_tokens({'from': accounts[1]})
    reward_gauge_wrapper.claim_tokens({'from': accounts[2]})

    expected = liquidity_gauge_reward.integrate_fraction(reward_gauge_wrapper)
    actual = token.balanceOf(accounts[1]) + token.balanceOf(accounts[2])

    assert expected > 0
    assert 0 <= expected - actual <= 1


def test_claim_reward_multiple(accounts, chain, liquidity_gauge_reward, reward_gauge_wrapper, coin_reward):
    reward_gauge_wrapper.deposit(1e18, {'from': accounts[1]})

    chain.sleep(WEEK // 2)
    reward_gauge_wrapper.deposit(10**18, {'from': accounts[2]})
    chain.sleep(WEEK)

    reward_gauge_wrapper.claim_tokens({'from': accounts[1]})
    reward_gauge_wrapper.claim_tokens({'from': accounts[2]})

    assert coin_reward.balanceOf(reward_gauge_wrapper) <= 1
    assert 0.9999 < coin_reward.balanceOf(accounts[2]) * 3 / coin_reward.balanceOf(accounts[1]) <= 1


def test_multiple_claims(accounts, chain, liquidity_gauge_reward, reward_gauge_wrapper, token):
    reward_gauge_wrapper.deposit(1e18, {'from': accounts[1]})

    chain.sleep(MONTH)
    reward_gauge_wrapper.claim_tokens({'from': accounts[1]})
    balance = token.balanceOf(accounts[1])

    chain.sleep(MONTH)
    reward_gauge_wrapper.claim_tokens({'from': accounts[1]})
    expected = liquidity_gauge_reward.integrate_fraction(reward_gauge_wrapper)
    final_balance = token.balanceOf(accounts[1])

    assert final_balance > balance
    assert final_balance == expected


def test_multiple_claims_reward(accounts, chain, liquidity_gauge_reward, reward_gauge_wrapper, coin_reward):
    reward_gauge_wrapper.deposit(1e18, {'from': accounts[1]})

    chain.sleep(86400)
    reward_gauge_wrapper.claim_tokens({'from': accounts[1]})
    balance = coin_reward.balanceOf(accounts[1])

    chain.sleep(86400)
    reward_gauge_wrapper.claim_tokens({'from': accounts[1]})
    expected = liquidity_gauge_reward.claimed_rewards_for(reward_gauge_wrapper)
    final_balance = coin_reward.balanceOf(accounts[1])

    assert final_balance > balance
    assert final_balance == expected


def test_claim_without_deposit(accounts, chain, reward_gauge_wrapper, token, coin_reward):
    reward_gauge_wrapper.claim_tokens({'from': accounts[1]})

    assert token.balanceOf(accounts[1]) == 0
    assert coin_reward.balanceOf(accounts[1]) == 0


def test_claimable_no_deposit(accounts, reward_gauge_wrapper):
    assert reward_gauge_wrapper.claimable_tokens.call(accounts[1]) == 0
    assert reward_gauge_wrapper.claimable_reward(accounts[1]) == 0


def test_claimable_tokens(accounts, chain, reward_gauge_wrapper, token):
    reward_gauge_wrapper.deposit(1e18, {'from': accounts[1]})

    chain.sleep(MONTH)
    chain.mine()
    claimable = reward_gauge_wrapper.claimable_tokens.call(accounts[1])

    reward_gauge_wrapper.claim_tokens({'from': accounts[1]})
    assert token.balanceOf(accounts[1]) >= claimable > 0


def test_claimable_reward(accounts, chain, reward_gauge_wrapper, coin_reward):
    reward_gauge_wrapper.deposit(1e18, {'from': accounts[1]})

    chain.sleep(MONTH)
    chain.mine()
    claimable = reward_gauge_wrapper.claimable_reward(accounts[1])

    reward_gauge_wrapper.claim_tokens({'from': accounts[1]})
    assert coin_reward.balanceOf(accounts[1]) == claimable
