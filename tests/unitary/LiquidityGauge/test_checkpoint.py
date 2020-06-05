import brownie


def test_user_checkpoint_wrong_account(accounts, liquidity_gauge):
    with brownie.reverts("dev: unauthorized"):
        liquidity_gauge.user_checkpoint(accounts[2], {'from': accounts[1]})
