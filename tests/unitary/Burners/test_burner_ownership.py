import brownie


def test_commit_transfer_ownership(burner, alice, bob):
    burner.commit_transfer_ownership(bob, {'from': alice})

    assert burner.owner() == alice
    assert burner.future_owner() == bob


def test_accept_transfer_ownership(burner, alice, bob):
    burner.commit_transfer_ownership(bob, {'from': alice})
    burner.accept_transfer_ownership({'from': bob})

    assert burner.owner() == bob
    assert burner.future_owner() == bob


def test_commit_twice_without_accept(burner, alice, bob):
    burner.commit_transfer_ownership(bob, {'from': alice})
    burner.commit_transfer_ownership(alice, {'from': alice})

    assert burner.owner() == alice
    assert burner.future_owner() == alice


def test_commit_only_owner(burner, alice, bob):
    with brownie.reverts("dev: only owner"):
        burner.commit_transfer_ownership(bob, {'from': bob})


def test_accept_only_owner(burner, alice, bob):
    burner.commit_transfer_ownership(bob, {'from': alice})
    with brownie.reverts("dev: only owner"):
        burner.accept_transfer_ownership({'from': alice})


def test_commit_transfer_emergency_ownership(burner, alice, bob):
    burner.commit_transfer_emergency_ownership(alice, {'from': bob})

    assert burner.emergency_owner() == bob
    assert burner.future_emergency_owner() == alice


def test_accept_transfer_emergency_ownership(burner, alice, bob):
    burner.commit_transfer_emergency_ownership(alice, {'from': bob})
    burner.accept_transfer_emergency_ownership({'from': alice})

    assert burner.emergency_owner() == alice
    assert burner.future_emergency_owner() == alice


def test_commit_twice_without_accept_emergency(burner, alice, bob):
    burner.commit_transfer_emergency_ownership(alice, {'from': bob})
    burner.commit_transfer_emergency_ownership(bob, {'from': bob})

    assert burner.emergency_owner() == bob
    assert burner.future_emergency_owner() == bob


def test_commit_emergency_only_owner(burner, alice):
    with brownie.reverts("dev: only owner"):
        burner.commit_transfer_emergency_ownership(alice, {'from': alice})


def test_accept_emergency_only_owner(burner, alice, bob):
    burner.commit_transfer_emergency_ownership(alice, {'from': bob})
    with brownie.reverts("dev: only owner"):
        burner.accept_transfer_emergency_ownership({'from': bob})
