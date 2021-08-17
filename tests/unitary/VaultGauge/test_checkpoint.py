import brownie

YEAR = 86400 * 365


def test_user_checkpoint(accounts, vault_gauge):
    vault_gauge.user_checkpoint(accounts[1], {"from": accounts[1]})


def test_user_checkpoint_new_period(accounts, chain, vault_gauge):
    vault_gauge.user_checkpoint(accounts[1], {"from": accounts[1]})
    chain.sleep(int(YEAR * 1.1))
    vault_gauge.user_checkpoint(accounts[1], {"from": accounts[1]})


def test_user_checkpoint_wrong_account(accounts, vault_gauge):
    with brownie.reverts("dev: unauthorized"):
        vault_gauge.user_checkpoint(accounts[2], {"from": accounts[1]})
