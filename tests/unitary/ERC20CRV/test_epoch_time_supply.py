import brownie

WEEK = 86400 * 7
YEAR = 365 * 86400


def test_start_epoch_time_write(token, rpc, accounts):
    creation_time = token.start_epoch_time()
    rpc.sleep(YEAR)
    rpc.mine()

    # the constant function should not report a changed value
    assert token.start_epoch_time() == creation_time

    # the state-changing function should show the changed value
    assert token.start_epoch_time_write().return_value == creation_time + YEAR

    # after calling the state-changing function, the view function is changed
    assert token.start_epoch_time() == creation_time + YEAR


def test_start_epoch_time_write_same_epoch(token, rpc, accounts):
    # calling `start_epoch_token_write` within the same epoch should not raise
    token.start_epoch_time_write()
    token.start_epoch_time_write()


def test_update_mining_parameters(token, rpc, accounts):
    creation_time = token.start_epoch_time()
    new_epoch = creation_time + YEAR - rpc.time()
    rpc.sleep(new_epoch)
    token.update_mining_parameters({'from': accounts[0]})


def test_update_mining_parameters_same_epoch(token, rpc, accounts):
    creation_time = token.start_epoch_time()
    new_epoch = creation_time + YEAR - rpc.time()
    rpc.sleep(new_epoch - 3)
    with brownie.reverts("dev: too soon!"):
        token.update_mining_parameters({'from': accounts[0]})


def test_mintable_in_timeframe_end_before_start(token, accounts):
    creation_time = token.start_epoch_time()
    with brownie.reverts("dev: start > end"):
        token.mintable_in_timeframe(creation_time + 1, creation_time)


def test_mintable_in_timeframe_multiple_epochs(token, accounts):
    creation_time = token.start_epoch_time()

    # two epochs should not raise
    token.mintable_in_timeframe(creation_time, int(creation_time + YEAR * 1.9))

    with brownie.reverts("dev: too far in future"):
        # three epochs should raise
        token.mintable_in_timeframe(creation_time, int(creation_time + YEAR * 2.1))


def test_available_supply(rpc, web3, token):
    creation_time = token.start_epoch_time()
    initial_supply = token.totalSupply()
    rate = token.rate()
    rpc.sleep(WEEK)
    rpc.mine()

    expected = initial_supply + (web3.eth.getBlock('latest')['timestamp'] - creation_time) * rate
    assert token.available_supply() == expected
