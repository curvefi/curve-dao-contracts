import brownie

WEEK = 86400 * 7


def test_start_epoch_time_write(accounts, chain, three_gauges, minter, token):
    creation_time = minter.start_epoch_time()
    chain.sleep(WEEK)
    chain.mine()

    # the constant function should not report a changed value
    assert minter.start_epoch_time() == creation_time

    # the state-changing function should show the changed value
    assert minter.start_epoch_time_write().return_value == creation_time + WEEK

    # after calling the state-changing function, the view function is changed
    assert minter.start_epoch_time() == creation_time + WEEK


def test_start_epoch_time_write_same_epoch(accounts, chain, three_gauges, minter, token):
    # calling `start_epoch_token_write` within the same epoch should not raise
    minter.start_epoch_time_write()
    minter.start_epoch_time_write()


def test_update_mining_parameters(accounts, chain, three_gauges, minter, token):
    creation_time = minter.start_epoch_time()
    new_epoch = creation_time + WEEK - chain.time()
    chain.sleep(new_epoch)
    minter.update_mining_parameters({"from": accounts[0]})


def test_update_mining_parameters_same_epoch(accounts, chain, three_gauges, minter, token):
    creation_time = minter.start_epoch_time()
    new_epoch = creation_time + WEEK - chain.time()
    chain.sleep(new_epoch - 3)
    with brownie.reverts("dev: too soon!"):
        minter.update_mining_parameters({"from": accounts[0]})
