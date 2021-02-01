import brownie


def test_recover_balance(burner, alice, receiver, coin_a):
    coin_a._mint_for_testing(10 ** 18, {"from": burner})

    burner.recover_balance(coin_a, {"from": alice})

    assert coin_a.balanceOf(burner) == 0
    assert coin_a.balanceOf(receiver) == 10 ** 18


def test_recover_balance_emergency_owner(burner, bob, receiver, coin_a):
    coin_a._mint_for_testing(10 ** 18, {"from": burner})

    burner.recover_balance(coin_a, {"from": bob})

    assert coin_a.balanceOf(burner) == 0
    assert coin_a.balanceOf(receiver) == 10 ** 18


def test_recover_only_owner(burner, coin_a, charlie):
    with brownie.reverts("dev: only owner"):
        burner.recover_balance(coin_a, {"from": charlie})


def test_set_recovery(alice, bob, receiver, burner):
    assert burner.recovery() == receiver

    burner.set_recovery(bob, {"from": alice})

    assert burner.recovery() == bob


def test_emergency_admin_cannot_set_recover(alice, bob, receiver, burner):
    with brownie.reverts("dev: only owner"):
        burner.set_recovery(bob, {"from": bob})
