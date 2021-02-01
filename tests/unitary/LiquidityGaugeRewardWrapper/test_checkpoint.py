import brownie
import pytest

YEAR = 86400 * 365


@pytest.fixture(scope="module", autouse=True)
def setup(accounts, gauge_controller, minter, liquidity_gauge_reward, token):
    token.set_minter(minter, {"from": accounts[0]})

    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": accounts[0]})
    gauge_controller.add_gauge(liquidity_gauge_reward, 0, 0, {"from": accounts[0]})


def test_user_checkpoint(accounts, reward_gauge_wrapper):
    reward_gauge_wrapper.user_checkpoint(accounts[1], {"from": accounts[1]})


def test_user_checkpoint_new_period(accounts, chain, reward_gauge_wrapper):
    reward_gauge_wrapper.user_checkpoint(accounts[1], {"from": accounts[1]})
    chain.sleep(int(YEAR * 1.1))
    reward_gauge_wrapper.user_checkpoint(accounts[1], {"from": accounts[1]})


def test_user_checkpoint_wrong_account(accounts, reward_gauge_wrapper):
    with brownie.reverts("dev: unauthorized"):
        reward_gauge_wrapper.user_checkpoint(accounts[2], {"from": accounts[1]})
