import pylab  # Requires matplotlib

from time import time
from datetime import datetime
from brownie import Contract

WEEK = 86400 * 7


def main():
    distributor = Contract("0xA464e6DCda8AC41e03616F95f4BC98a13b8922Dc")
    tri_pool = Contract("0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7")
    t = int(time()) // WEEK * WEEK
    virtual_price = tri_pool.get_virtual_price() / 1e18

    output = []
    while True:
        fees = distributor.tokens_per_week(t)
        if fees == 0 and len(output) > 0:
            break
        d = datetime.fromtimestamp(t)
        output.append((d, fees))
        t -= WEEK
    if output[0][1] == 0:
        output = output[1:]
    dates = []
    fees = []
    for d, fee in output[::-1]:
        dates.append(d)
        fees.append(fee * virtual_price / 1e18)
        print("{0}|\t${1:.2f}".format(d, fees[-1]))

    pylab.bar(range(len(fees)), fees)
    pylab.xlabel("Distribution date")
    pylab.ylabel("Fees distributed")
    pylab.xticks(range(len(dates)), [d.strftime("%d-%m-%y") for d in dates])
    pylab.ylim(0, max(fees) * 1.1)
    pylab.show()
