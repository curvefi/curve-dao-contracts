import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def initial_funding(coin_a, vesting_factory, accounts):
    coin_a._mint_for_testing(10**21, {'from': accounts[0]})
    coin_a.transfer(vesting_factory, 10**21, {'from': accounts[0]})


def test_admin_only(VestingEscrowSimple, accounts, vesting_factory, coin_a, start_time, end_time):
    with brownie.reverts("dev: admin only"):
        vesting_factory.deploy_vesting_contract(
            coin_a, accounts[1], 10**18, start_time, end_time, True, {'from': accounts[1]}
        )


def test_approve_fail(VestingEscrowSimple, accounts, vesting_factory, coin_a, start_time, end_time):
    with brownie.reverts("dev: approve failed"):
        vesting_factory.deploy_vesting_contract(
            ZERO_ADDRESS, accounts[1], 10**18, start_time, end_time, True, {'from': accounts[0]}
        )


def test_start_before_now(VestingEscrowSimple, accounts, chain, vesting_factory, coin_a, end_time):
    with brownie.reverts():
        vesting_factory.deploy_vesting_contract(
            coin_a, accounts[1], 10**18, chain.time() - 5, end_time, True, {'from': accounts[0]}
        )


def test_end_before_start(VestingEscrowSimple, accounts, vesting_factory, coin_a, start_time):
    with brownie.reverts():
        vesting_factory.deploy_vesting_contract(
            coin_a, accounts[1], 10**18, start_time, start_time - 1, True, {'from': accounts[0]}
        )


def test_target_is_set(vesting_factory, vesting_target):
    assert vesting_factory.target() == vesting_target


def test_deploys(VestingEscrowSimple, accounts, vesting_factory, coin_a, start_time, end_time):
    tx = vesting_factory.deploy_vesting_contract(
        coin_a, accounts[1], 10**18, start_time, end_time, True, {'from': accounts[0]}
    )

    assert len(tx.new_contracts) == 1
    assert tx.return_value == tx.new_contracts[0]


def test_token_xfer(vesting_simple, coin_a):
    # exactly 10**18 tokens should be transferred
    assert coin_a.balanceOf(vesting_simple) == 10**20


def test_token_approval(vesting_simple, vesting_factory, coin_a):
    # remaining approval should be zero
    assert coin_a.allowance(vesting_simple, vesting_factory) == 0


def test_init_vars(vesting_simple, accounts, coin_a, start_time, end_time):
    assert vesting_simple.token() == coin_a
    assert vesting_simple.admin() == accounts[0]
    assert vesting_simple.start_time() == start_time
    assert vesting_simple.end_time() == end_time
    assert vesting_simple.can_disable() is True
    assert vesting_simple.initial_locked(accounts[1]) == 10**20


def test_cannot_call_init(vesting_simple, accounts, coin_a, start_time, end_time):
    with brownie.reverts("dev: can only initialize once"):
        vesting_simple.initialize(
            accounts[0],
            coin_a,
            accounts[1],
            10**20,
            start_time,
            end_time,
            True,
            {'from': accounts[0]},
        )


def test_cannot_init_factory_target(vesting_target, accounts, coin_a, start_time, end_time):
    with brownie.reverts("dev: can only initialize once"):
        vesting_target.initialize(
            accounts[0],
            coin_a,
            accounts[1],
            10**20,
            start_time,
            end_time,
            True,
            {'from': accounts[0]},
        )
