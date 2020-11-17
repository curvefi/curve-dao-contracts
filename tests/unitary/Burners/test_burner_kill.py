import brownie


def test_owner_can_kill(burner, alice):
    burner.set_killed(True, {'from': alice})

    assert burner.is_killed()


def test_emergency_owner_can_kill(burner, bob):
    burner.set_killed(True, {'from': bob})

    assert burner.is_killed()


def test_kill_and_unkill(burner, alice):
    burner.set_killed(True, {'from': alice})
    burner.set_killed(False, {'from': alice})

    assert not burner.is_killed()


def test_only_owner_can_kill(burner, charlie):
    with brownie.reverts("dev: only owner"):
        burner.set_killed(True, {'from': charlie})


def test_cannot_burn_when_killed(burner, alice):
    burner.set_killed(True, {'from': alice})
    with brownie.reverts("dev: is killed"):
        burner.burn(alice, {'from': alice})

    if hasattr(burner, "execute"):
        with brownie.reverts("dev: is killed"):
            burner.execute({'from': alice})
