import pytest
from brownie import ZERO_ADDRESS

from tests.conftest import approx

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


@pytest.fixture(scope="module")
def reward_contract(RewardStream, alice, charlie, rewards_only_gauge, coin_reward):
    contract = RewardStream.deploy(alice, charlie, coin_reward, 86400 * 7, {"from": alice})
    contract.add_receiver(rewards_only_gauge, {"from": alice})
    coin_reward.approve(contract, 2 ** 256 - 1, {"from": charlie})
    coin_reward._mint_for_testing(charlie, REWARD, {"from": alice})
    return contract


@pytest.fixture(scope="module", autouse=True)
def initial_setup(
    alice,
    bob,
    charlie,
    chain,
    coin_reward,
    reward_contract,
    token,
    mock_lp_token,
    rewards_only_gauge,
    gauge_controller,
    minter,
):
    # gauge setup
    token.set_minter(minter, {"from": alice})
    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": alice})
    gauge_controller.add_gauge(rewards_only_gauge, 0, 0, {"from": alice})

    # deposit into gauge
    mock_lp_token.transfer(bob, LP_AMOUNT, {"from": alice})
    mock_lp_token.approve(rewards_only_gauge, LP_AMOUNT, {"from": bob})
    rewards_only_gauge.deposit(LP_AMOUNT, {"from": bob})

    # add rewards
    sigs = reward_contract.get_reward.signature
    rewards_only_gauge.set_rewards(
        reward_contract, sigs, [coin_reward] + [ZERO_ADDRESS] * 7, {"from": alice}
    )

    # fund rewards
    reward_contract.notify_reward_amount(REWARD, {"from": charlie})


def test_claim_one_lp(bob, chain, rewards_only_gauge, coin_reward):
    chain.sleep(WEEK)

    rewards_only_gauge.withdraw(LP_AMOUNT, {"from": bob})
    rewards_only_gauge.claim_rewards({"from": bob})

    reward = coin_reward.balanceOf(bob)
    assert reward <= REWARD
    assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other(bob, charlie, chain, rewards_only_gauge, coin_reward):
    chain.sleep(WEEK)

    rewards_only_gauge.withdraw(LP_AMOUNT, {"from": bob})
    rewards_only_gauge.claim_rewards(bob, {"from": charlie})

    assert coin_reward.balanceOf(charlie) == 0

    reward = coin_reward.balanceOf(bob)
    assert reward <= REWARD
    assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other_no_reward(bob, charlie, chain, rewards_only_gauge, coin_reward):
    chain.sleep(WEEK)
    rewards_only_gauge.claim_rewards(charlie, {"from": bob})

    assert coin_reward.balanceOf(bob) == 0
    assert coin_reward.balanceOf(charlie) == 0


def test_claim_two_lp(
    alice, bob, chain, rewards_only_gauge, mock_lp_token, coin_reward, no_call_coverage
):

    # Deposit
    mock_lp_token.approve(rewards_only_gauge, LP_AMOUNT, {"from": alice})
    rewards_only_gauge.deposit(LP_AMOUNT, {"from": alice})

    chain.sleep(WEEK)
    chain.mine()

    # Calculate rewards
    claimable_rewards = [
        rewards_only_gauge.claimable_reward_write.call(acc, coin_reward, {"from": acc})
        for acc in (alice, bob)
    ]

    # Claim rewards
    rewards = []
    for acct in (alice, bob):
        rewards_only_gauge.claim_rewards({"from": acct})
        rewards += [coin_reward.balanceOf(acct)]

    # Calculation == results
    assert tuple(claimable_rewards) == tuple(rewards)

    # Approximately equal apart from what caused by 1 s ganache-cli jitter
    assert sum(rewards) <= REWARD
    assert approx(sum(rewards), REWARD, 1.001 / WEEK)  # ganache-cli jitter of 1 s
    assert approx(rewards[0], rewards[1], 2.002 * WEEK)


def test_claimable_rewards_write_retrieves_rewards(
    alice, chain, rewards_only_gauge, mock_lp_token, coin_reward, no_call_coverage
):

    # Deposit
    mock_lp_token.approve(rewards_only_gauge, LP_AMOUNT, {"from": alice})
    rewards_only_gauge.deposit(LP_AMOUNT, {"from": alice})

    chain.sleep(WEEK)
    chain.mine()

    before = coin_reward.balanceOf(rewards_only_gauge)
    rewards_only_gauge.claimable_reward_write(alice, coin_reward, {"from": alice})
    assert before < coin_reward.balanceOf(rewards_only_gauge)
