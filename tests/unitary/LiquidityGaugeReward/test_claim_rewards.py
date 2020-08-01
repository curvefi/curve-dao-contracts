REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


def test_claim_no_deposit(accounts, chain, liquidity_gauge_reward, mock_lp_token,
                          reward_contract, coin_reward):
    coin_reward._mint_for_testing(REWARD, {'from': accounts[0]})
    coin_reward.transfer(reward_contract, REWARD, {'from': accounts[0]})
    reward_contract.notifyRewardAmount(REWARD, {'from': accounts[0]})

    chain.sleep(WEEK)

    liquidity_gauge_reward.claim_rewards({'from': accounts[1]})

    assert coin_reward.balanceOf(accounts[1]) == 0


def test_claim_no_rewards(accounts, chain, liquidity_gauge_reward, mock_lp_token,
                          reward_contract, coin_reward):
    mock_lp_token.transfer(accounts[1], LP_AMOUNT, {'from': accounts[0]})
    mock_lp_token.approve(liquidity_gauge_reward, LP_AMOUNT, {'from': accounts[1]})
    liquidity_gauge_reward.deposit(LP_AMOUNT, {'from': accounts[1]})

    chain.sleep(WEEK)

    liquidity_gauge_reward.withdraw(LP_AMOUNT, {'from': accounts[1]})
    liquidity_gauge_reward.claim_rewards({'from': accounts[1]})

    assert coin_reward.balanceOf(accounts[1]) == 0
