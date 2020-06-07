import brownie

WEEK = 86400 * 7
YEAR = 365 * 86400
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_burner_only(accounts, token):
    with brownie.reverts("Only burner is allowed to burn"):
        token.burn(0, {'from': accounts[1]})


def test_burnFrom_burner_only(accounts, token):
    with brownie.reverts("Only burner is allowed to burn"):
        token.burnFrom(accounts[0], 0, {'from': accounts[1]})


def test_zero_address(accounts, token):
    with brownie.reverts("dev: zero address"):
        token.burnFrom(ZERO_ADDRESS, 0, {'from': accounts[0]})


def test_burn(accounts, token):
    balance = token.balanceOf(accounts[0])
    initial_supply = token.totalSupply()
    token.burn(31337, {'from': accounts[0]})

    assert token.balanceOf(accounts[0]) == balance - 31337
    assert token.totalSupply() == initial_supply - 31337


def test_burnFrom(accounts, token):
    initial_supply = token.totalSupply()
    token.transfer(accounts[1], 10000000, {'from': accounts[0]})
    token.burnFrom(accounts[1], 31337, {'from': accounts[0]})

    assert token.balanceOf(accounts[1]) == 10000000 - 31337
    assert token.totalSupply() == initial_supply - 31337


def test_burn_all(accounts, token):
    initial_supply = token.totalSupply()
    token.burn(initial_supply, {'from': accounts[0]})

    assert token.balanceOf(accounts[0]) == 0
    assert token.totalSupply() == 0


def test_overburn(accounts, token):
    initial_supply = token.totalSupply()

    with brownie.reverts("Integer underflow"):
        token.burn(initial_supply + 1, {'from': accounts[0]})
