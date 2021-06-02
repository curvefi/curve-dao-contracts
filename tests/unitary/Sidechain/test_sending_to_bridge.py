from brownie import ETH_ADDRESS, web3
from brownie.convert import to_bytes
from hexbytes import HexBytes

WEEK = 86400 * 7


def test_anyswap_root_gauge_transfer_crv(alice, chain, gauge_controller, anyswap_root_gauge, token):
    gauge_controller.add_type("Test", 10 ** 18, {"from": alice})
    gauge_controller.add_gauge(anyswap_root_gauge, 0, 1, {"from": alice})

    chain.mine(timedelta=2 * WEEK)

    amount = token.rate() * WEEK

    tx = anyswap_root_gauge.checkpoint()

    transfer_subcall = tx.subcalls[-1]

    assert transfer_subcall["function"] == "transfer(address,uint256)"
    assert transfer_subcall["to"] == token
    assert list(transfer_subcall["inputs"].values()) == [ETH_ADDRESS, amount]

    assert token.balanceOf(ETH_ADDRESS) == amount


def test_polygon_root_gauge_transfer_crv(alice, chain, gauge_controller, polygon_root_gauge, token):
    gauge_controller.add_type("Test", 10 ** 18, {"from": alice})
    gauge_controller.add_gauge(polygon_root_gauge, 0, 1, {"from": alice})

    chain.mine(timedelta=2 * WEEK)

    amount = token.rate() * WEEK

    tx = polygon_root_gauge.checkpoint()

    # since we use a raw call won't show up in subcalls but we can check the trace
    # and values in memory at the time of the call
    deposit_for_call_memory = list(filter(lambda t: t["op"] == "CALL", tx.trace))[-1]["memory"]
    memory = HexBytes("".join(deposit_for_call_memory))
    # our expectation of what should be at the end of memory
    # mirror of what is in the source code
    # pad the end with 28 empty bytes, because we have the fn selector at the beginning
    expected_data = (
        web3.keccak(text="depositFor(address,address,bytes)")[:4]
        + to_bytes(HexBytes(polygon_root_gauge.address))
        + to_bytes(HexBytes(token.address))
        + to_bytes(96)
        + to_bytes(32)
        + to_bytes(amount)
        + (0).to_bytes(28, "big")
    )

    data_length = len(expected_data)
    # check that we are calling the bridge addr with the appropriate data
    assert memory[-data_length:] == expected_data


def test_xdai_root_gauge_transfer_crv(alice, chain, gauge_controller, xdai_root_gauge, token):
    gauge_controller.add_type("Test", 10 ** 18, {"from": alice})
    gauge_controller.add_gauge(xdai_root_gauge, 0, 1, {"from": alice})

    chain.mine(timedelta=2 * WEEK)

    amount = token.rate() * WEEK

    tx = xdai_root_gauge.checkpoint()

    # since we use a raw call won't show up in subcalls but we can check the trace
    # and values in memory at the time of the call
    relay_tokens_call_memory = list(filter(lambda t: t["op"] == "CALL", tx.trace))[-1]["memory"]
    memory = HexBytes("".join(relay_tokens_call_memory))
    # our expectation of what should be at the end of memory
    # mirror of what is in the source code
    # pad the end with 28 empty bytes, because we have the fn selector at the beginning
    expected_data = (
        web3.keccak(text="relayTokens(address,address,uint256)")[:4]
        + to_bytes(HexBytes(token.address))
        + to_bytes(HexBytes(xdai_root_gauge.address))
        + to_bytes(amount)
        + (0).to_bytes(28, "big")
    )

    data_length = len(expected_data)
    # check that we are calling the bridge addr with the appropriate data
    assert memory[-data_length:] == expected_data
