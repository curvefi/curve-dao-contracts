import pytest
from eth_tester.exceptions import TransactionFailed
from random import random
from math import log10
from .conftest import time_travel


def test_mintable_in_timeframe(w3, token):
    owner = w3.eth.accounts[0]
    from_owner = {'from': owner}

    # Sometimes can go across epochs
    for i in range(10):
        dt = int(10 ** (random() * log10(300 * 86400)))
        t0 = token.caller.start_epoch_time()
        t1 = time_travel(w3, dt)
        if t1 - t0 >= 365 * 86400:
            token.functions.update_mining_parameters().transact(from_owner)
        else:
            with pytest.raises(TransactionFailed):
                token.functions.update_mining_parameters().transact(from_owner)
