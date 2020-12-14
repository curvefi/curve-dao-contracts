import brownie

YEAR = 86400 * 365


def test_user_checkpoint(accounts, gauge_v2):
    gauge_v2.user_checkpoint(accounts[1], {'from': accounts[1]})


def test_user_checkpoint_new_period(accounts, chain, gauge_v2):
    gauge_v2.user_checkpoint(accounts[1], {'from': accounts[1]})
    chain.sleep(int(YEAR * 1.1))
    gauge_v2.user_checkpoint(accounts[1], {'from': accounts[1]})


def test_user_checkpoint_wrong_account(accounts, gauge_v2):
    with brownie.reverts("dev: unauthorized"):
        gauge_v2.user_checkpoint(accounts[2], {'from': accounts[1]})
