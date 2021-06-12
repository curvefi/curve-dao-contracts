from itertools import product

import brownie
import pytest


@pytest.mark.parametrize("commit,accept", product([0, 1], repeat=2))
def test_change_ownership(alice, charlie, commit, accept, stream):
    if commit:
        stream.commit_transfer_ownership(charlie, {"from": alice})

        if accept:
            stream.accept_transfer_ownership({"from": charlie})

    assert stream.owner() == charlie if commit and accept else alice


def test_commit_only_owner(charlie, stream):
    with brownie.reverts("dev: only owner"):
        stream.commit_transfer_ownership(charlie, {"from": charlie})


def test_accept_only_owner(alice, bob, stream):
    stream.commit_transfer_ownership(bob, {"from": alice})

    with brownie.reverts("dev: only new owner"):
        stream.accept_transfer_ownership({"from": alice})
