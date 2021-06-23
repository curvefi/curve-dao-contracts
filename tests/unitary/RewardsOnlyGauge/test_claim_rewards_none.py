from brownie import ZERO_ADDRESS

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


def test_claim_no_deposit(
    alice, bob, chain, rewards_only_gauge, mock_lp_token, reward_contract, coin_reward
):
    # Fund
    mock_lp_token.approve(rewards_only_gauge, LP_AMOUNT, {"from": alice})
    rewards_only_gauge.deposit(LP_AMOUNT, {"from": alice})

    coin_reward._mint_for_testing(reward_contract, REWARD)
    reward_contract.notifyRewardAmount(REWARD, {"from": alice})

    rewards_only_gauge.set_rewards(
        reward_contract,
        "0x3d18b912",
        [coin_reward] + [ZERO_ADDRESS] * 7,
        {"from": alice},
    )

    chain.sleep(WEEK)

    rewards_only_gauge.claim_rewards({"from": bob})

    assert coin_reward.balanceOf(bob) == 0


def test_claim_no_rewards(
    alice, bob, chain, rewards_only_gauge, mock_lp_token, reward_contract, coin_reward
):
    # Deposit
    mock_lp_token.transfer(bob, LP_AMOUNT, {"from": alice})
    mock_lp_token.approve(rewards_only_gauge, LP_AMOUNT, {"from": bob})
    rewards_only_gauge.deposit(LP_AMOUNT, {"from": bob})

    chain.sleep(WEEK)

    rewards_only_gauge.withdraw(LP_AMOUNT, {"from": bob})
    rewards_only_gauge.claim_rewards({"from": bob})

    assert coin_reward.balanceOf(bob) == 0
