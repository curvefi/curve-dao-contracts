import pytest
from brownie import ZERO_ADDRESS, compile_source

from tests.conftest import approx

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


code = """
# @version 0.2.7

from vyper.interfaces import ERC20

first: address
second: address

@external
def __init__(_first: address, _second: address):
    self.first = _first
    self.second = _second

@external
def claim_tokens() -> bool:
    ERC20(self.first).transfer(msg.sender, ERC20(self.first).balanceOf(self))
    ERC20(self.second).transfer(msg.sender, ERC20(self.second).balanceOf(self))

    return True
"""


@pytest.fixture(scope="module")
def reward_contract(alice, coin_a, coin_b):
    contract = compile_source(code).Vyper.deploy(coin_a, coin_b, {'from': alice})
    coin_a._mint_for_testing(REWARD, {'from': contract})
    coin_b._mint_for_testing(REWARD, {'from': contract})

    yield contract


@pytest.fixture(scope="module", autouse=True)
def initial_setup(
    alice, bob, chain, gauge_v2, reward_contract, coin_reward, coin_a, coin_b, mock_lp_token
):

    sigs = f"0x{'00' * 4}{'00' * 4}{reward_contract.claim_tokens.signature[2:]}{'00' * 20}"

    gauge_v2.set_rewards(
        reward_contract,
        sigs,
        [coin_a, coin_reward, coin_b] + [ZERO_ADDRESS] * 5,
        {'from': alice}
    )

    # Deposit
    mock_lp_token.transfer(bob, LP_AMOUNT, {'from': alice})
    mock_lp_token.approve(gauge_v2, LP_AMOUNT, {'from': bob})
    gauge_v2.deposit(LP_AMOUNT, {'from': bob})


def test_claim_one_lp(bob, chain, gauge_v2, coin_a, coin_b):
    chain.sleep(WEEK)

    gauge_v2.withdraw(LP_AMOUNT, {'from': bob})
    gauge_v2.claim_rewards({'from': bob})

    for coin in (coin_a, coin_b):
        reward = coin.balanceOf(bob)
        assert reward <= REWARD
        assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other(bob, charlie, chain, gauge_v2, coin_a, coin_b):
    chain.sleep(WEEK)

    gauge_v2.withdraw(LP_AMOUNT, {'from': bob})
    gauge_v2.claim_rewards(bob, {'from': charlie})

    assert coin_a.balanceOf(charlie) == 0

    for coin in (coin_a, coin_b):
        reward = coin.balanceOf(bob)
        assert reward <= REWARD
        assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other_no_reward(bob, charlie, chain, gauge_v2, coin_a, coin_b):
    chain.sleep(WEEK)
    gauge_v2.claim_rewards(charlie, {'from': bob})

    assert coin_a.balanceOf(bob) == 0
    assert coin_a.balanceOf(charlie) == 0

    assert coin_b.balanceOf(bob) == 0
    assert coin_b.balanceOf(charlie) == 0


def test_claim_two_lp(alice, bob, chain, gauge_v2, mock_lp_token,
                      coin_a, coin_b, reward_contract, no_call_coverage):

    # Deposit
    mock_lp_token.approve(gauge_v2, LP_AMOUNT, {'from': alice})
    gauge_v2.deposit(LP_AMOUNT, {'from': alice})

    coin_a._mint_for_testing(REWARD, {'from': reward_contract})
    coin_b._mint_for_testing(REWARD, {'from': reward_contract})

    chain.sleep(WEEK)
    chain.mine()

    for acct in (alice, bob):
        gauge_v2.claim_rewards({'from': acct})

    for coin in (coin_a, coin_b):
        # Calculate rewards
        assert coin.balanceOf(bob) > coin.balanceOf(alice) > 0
        assert coin.balanceOf(gauge_v2) == 0
