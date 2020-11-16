from brownie import ZERO_ADDRESS


REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


def test_claim_no_deposit(alice, bob, chain, gauge_v2, mock_lp_token, reward_contract, coin_reward):
    # Fund
    mock_lp_token.approve(gauge_v2, LP_AMOUNT, {'from': alice})
    gauge_v2.deposit(LP_AMOUNT, {'from': alice})

    coin_reward._mint_for_testing(REWARD, {'from': alice})
    coin_reward.transfer(reward_contract, REWARD, {'from': alice})
    reward_contract.notifyRewardAmount(REWARD, {'from': alice})

    gauge_v2.set_rewards(
        reward_contract,
        "0xa694fc3a2e1a7d4d3d18b9120000000000000000000000000000000000000000",
        [coin_reward] + [ZERO_ADDRESS] * 7,
        {'from': alice}
    )

    chain.sleep(WEEK)

    gauge_v2.claim_rewards({'from': bob})

    assert coin_reward.balanceOf(bob) == 0


def test_claim_no_rewards(alice, bob, chain, gauge_v2, mock_lp_token, reward_contract, coin_reward):
    # Deposit
    mock_lp_token.transfer(bob, LP_AMOUNT, {'from': alice})
    mock_lp_token.approve(gauge_v2, LP_AMOUNT, {'from': bob})
    gauge_v2.deposit(LP_AMOUNT, {'from': bob})

    chain.sleep(WEEK)

    gauge_v2.withdraw(LP_AMOUNT, {'from': bob})
    gauge_v2.claim_rewards({'from': bob})

    assert coin_reward.balanceOf(bob) == 0
