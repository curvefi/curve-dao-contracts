WEEK = 86400 * 7
YEAR = 365 * 86400


def test_rate(accounts, chain, distributor, token):
    assert distributor.rate() == 0

    chain.sleep(86401)
    distributor.update_mining_parameters({"from": accounts[0]})

    assert distributor.rate() > 0


def test_start_epoch_time(accounts, chain, distributor):
    creation_time = distributor.start_epoch_time()
    assert creation_time == distributor.tx.timestamp + 86400 - YEAR

    chain.sleep(86401)
    distributor.update_mining_parameters({"from": accounts[0]})

    assert distributor.start_epoch_time() == creation_time + YEAR


def test_mining_epoch(accounts, chain, distributor):
    assert distributor.mining_epoch() == -1

    chain.sleep(86401)
    distributor.update_mining_parameters({"from": accounts[0]})

    assert distributor.mining_epoch() == 0


def test_available_to_distribute(accounts, chain, distributor):
    assert distributor.avaialable_to_distribute() == 6000000 * 10 ** 18

    chain.sleep(86401)
    distributor.update_mining_parameters({"from": accounts[0]})

    assert distributor.avaialable_to_distribute() > 6000000 * 10 ** 18
