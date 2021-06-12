import pytest
from brownie_tokens import ERC20


@pytest.fixture(scope="module")
def reward_token(bob):
    token = ERC20()
    token._mint_for_testing(bob, 10 ** 19)
    return token


@pytest.fixture(scope="module")
def stream(RewardStream, alice, bob, reward_token):
    contract = RewardStream.deploy(alice, bob, reward_token, 86400 * 10, {"from": alice})
    reward_token.approve(contract, 2 ** 256 - 1, {"from": bob})
    return contract
