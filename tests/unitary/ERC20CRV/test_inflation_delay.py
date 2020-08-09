WEEK = 86400 * 7
YEAR = 365 * 86400


def test_rate(accounts, chain, token):
    assert token.rate() == 0

    chain.sleep(86401)
    token.update_mining_parameters({'from': accounts[0]})

    assert token.rate() > 0


def test_start_epoch_time(accounts, chain, token):
    creation_time = token.start_epoch_time()
    assert creation_time == token.tx.timestamp + 86400 - YEAR

    chain.sleep(86401)
    token.update_mining_parameters({'from': accounts[0]})

    assert token.start_epoch_time() == creation_time + YEAR


def test_mining_epoch(accounts, chain, token):
    assert token.mining_epoch() == -1

    chain.sleep(86401)
    token.update_mining_parameters({'from': accounts[0]})

    assert token.mining_epoch() == 0


def test_available_supply(accounts, chain, token):
    assert token.available_supply() == 1_272_727_273 * 10**18

    chain.sleep(86401)
    token.update_mining_parameters({'from': accounts[0]})

    assert token.available_supply() > 1_272_727_273 * 10**18
