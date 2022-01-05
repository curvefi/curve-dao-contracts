WEEK = 86400 * 7


def test_rate(accounts, chain, three_gauges, minter, token):
    assert minter.rate() == 0

    chain.sleep(86401)
    minter.update_mining_parameters({"from": accounts[0]})

    assert minter.rate() > 0

# changes to new rate
def test_commit_new_rate(accounts, chain, three_gauges, minter, token):
    chain.sleep(86401)
    minter.update_mining_parameters({"from": accounts[0]})

    assert minter.rate() == 761033399470899470

    minter.commit_new_rate(9_000_000, {"from": accounts[0]})
    assert minter.committed_rate() == 14880952380952380952
    assert minter.rate() == 761033399470899470

    chain.sleep(604801)
    minter.update_mining_parameters({"from": accounts[0]})
    assert minter.committed_rate() != 9_000_000 * 10 ** 18 / WEEK
    assert minter.rate() == 14880952380952380952

# changes to new rate
def test_commit_new_rate_zero(accounts, chain, three_gauges, minter, token):
    chain.sleep(86401)
    minter.update_mining_parameters({"from": accounts[0]})

    assert minter.rate() == 761033399470899470

    minter.commit_new_rate(0, {"from": accounts[0]})
    assert minter.committed_rate() == 0
    assert minter.rate() == 761033399470899470

    chain.sleep(604801)
    minter.update_mining_parameters({"from": accounts[0]})
    assert minter.committed_rate() != 0
    assert minter.rate() == 0

    chain.sleep(604801)
    minter.update_mining_parameters({"from": accounts[0]})
    assert minter.committed_rate() != 0
    assert minter.rate() == 0

def test_start_epoch_time(accounts, chain, three_gauges, minter, token):
    creation_time = minter.start_epoch_time()
    assert creation_time == minter.tx.timestamp + 86400 - WEEK

    chain.sleep(86401)
    minter.update_mining_parameters({"from": accounts[0]})

    assert minter.start_epoch_time() == creation_time + WEEK


def test_mining_epoch(accounts, chain, three_gauges, minter, token):
    assert minter.mining_epoch() == -1

    chain.sleep(86401)
    minter.update_mining_parameters({"from": accounts[0]})

    assert minter.mining_epoch() == 0
