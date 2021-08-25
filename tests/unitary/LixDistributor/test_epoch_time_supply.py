import brownie

WEEK = 86400 * 7
YEAR = 365 * 86400


def test_start_epoch_time_write(distributor, chain, accounts):
    creation_time = distributor.start_epoch_time()
    chain.sleep(YEAR)
    chain.mine()

    # the constant function should not report a changed value
    assert distributor.start_epoch_time() == creation_time

    # the state-changing function should show the changed value
    assert distributor.start_epoch_time_write().return_value == creation_time + YEAR

    # after calling the state-changing function, the view function is changed
    assert distributor.start_epoch_time() == creation_time + YEAR


def test_start_epoch_time_write_same_epoch(distributor, chain, accounts):
    # calling `start_epoch_token_write` within the same epoch should not raise
    first_write = distributor.start_epoch_time_write().return_value
    second_write = distributor.start_epoch_time_write().return_value

    assert first_write == second_write


def test_update_mining_parameters(distributor, chain, accounts):
    creation_time = distributor.start_epoch_time()
    new_epoch = creation_time + YEAR - chain.time()
    chain.sleep(new_epoch)
    distributor.update_mining_parameters({"from": accounts[0]})

    assert distributor.start_epoch_time() == creation_time + YEAR


def test_update_mining_parameters_same_epoch(distributor, chain, accounts):
    creation_time = distributor.start_epoch_time()
    new_epoch = creation_time + YEAR - chain.time()
    chain.sleep(new_epoch - 3)
    with brownie.reverts("dev: too soon!"):
        distributor.update_mining_parameters({"from": accounts[0]})


def test_distributable_in_timeframe_end_before_start(distributor, accounts):
    creation_time = distributor.start_epoch_time()
    with brownie.reverts("dev: start > end"):
        distributor.distributable_in_timeframe(creation_time + 1, creation_time)


def test_distributable_in_timeframe_multiple_epochs(distributor, accounts):
    creation_time = distributor.start_epoch_time()

    # two epochs should not raise
    distributor.distributable_in_timeframe(creation_time, int(creation_time + YEAR * 1.9))

    with brownie.reverts("dev: too far in future"):
        # three epochs should raise
        distributor.distributable_in_timeframe(creation_time, int(creation_time + YEAR * 2.1))


def test_avaialable_to_distribute(chain, web3, distributor):
    chain.sleep(WEEK)
    chain.mine()

    epoch_0_start = distributor.start_epoch_time_write().return_value
    rate = distributor.rate()
    initial_supply = 6000000 * 10 ** 18

    expected = initial_supply + (chain[-1].timestamp - epoch_0_start) * rate
    assert distributor.avaialable_to_distribute() == expected
