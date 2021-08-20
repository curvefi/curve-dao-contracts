import brownie

MAX_UINT256 = 2 ** 256 - 1
WEEK = 7 * 86400


def test_kick(chain, accounts, vault_gauge, voting_escrow, token, lixir_vault):
    alice, bob = accounts[:2]
    chain.sleep(2 * WEEK + 5)

    token.approve(voting_escrow, MAX_UINT256, {"from": alice})
    voting_escrow.create_lock(10 ** 20, chain.time() + 4 * WEEK, {"from": alice})

    lixir_vault.approve(vault_gauge.address, MAX_UINT256, {"from": alice})
    vault_gauge.deposit(10 ** 18, {"from": alice})

    assert vault_gauge.working_balances(alice) == 10 ** 18

    chain.sleep(WEEK)

    with brownie.reverts("dev: kick not allowed"):
        vault_gauge.kick(alice, {"from": bob})

    chain.sleep(4 * WEEK)

    vault_gauge.kick(alice, {"from": bob})
    assert vault_gauge.working_balances(alice) == 4 * 10 ** 17

    with brownie.reverts("dev: kick not needed"):
        vault_gauge.kick(alice, {"from": bob})
