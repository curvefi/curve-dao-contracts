def test_burner(WrappedBurner, WETH, alice, receiver):
    initial_balance = receiver.balance()
    burner = WrappedBurner.deploy(WETH, receiver, {"from": alice})
    amount = 12 * 10 ** 18
    WETH._mint_for_testing(alice, amount, {"from": alice})
    WETH.approve(burner, 2 ** 256 - 1, {"from": alice})
    WETH._mint_for_testing(burner, 2 * amount, {"from": alice})

    burner.burn(WETH, {"from": alice})

    assert burner.balance() == 0
    assert WETH.balanceOf(burner) == 0

    assert receiver.balance() - initial_balance == 3 * amount
    assert WETH.balanceOf(receiver) == 0
