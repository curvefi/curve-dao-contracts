REWARD = 10 ** 20
WEEK = 7 * 86400


def test_claim_no_deposit(accounts, chain, liquidity_gauge_reward, mock_lp_token,
                          reward_contract, coin_reward):
    coin_reward._mint_for_testing(REWARD, {'from': accounts[0]})
    coin_reward.transfer(reward_contract, REWARD, {'from': accounts[0]})
    reward_contract.notifyRewardAmount(REWARD, {'from': accounts[0]})

    chain.sleep(WEEK)

    liquidity_gauge_reward.claim_rewards({'from': accounts[1]})

    assert coin_reward.balanceOf(accounts[1]) == 0
