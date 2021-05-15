from brownie import ZERO_ADDRESS


def test_checkpoint_single(alice, root_gauge, checkpoint_proxy):
    tx = checkpoint_proxy.checkpoint(root_gauge, {"from": alice})

    assert tx.return_value is True

    assert tx.subcalls[0]["function"] == "checkpoint()"
    assert tx.subcalls[0]["to"] == root_gauge


def test_checkpoint_many(
    alice, checkpoint_proxy, anyswap_root_gauge, polygon_root_gauge, xdai_root_gauge
):
    gauges = [anyswap_root_gauge, polygon_root_gauge, xdai_root_gauge] + [ZERO_ADDRESS] * 7
    tx = checkpoint_proxy.checkpoint_many(gauges, {"from": alice})

    assert tx.return_value is True

    for i in range(3):
        assert tx.subcalls[i]["function"] == "checkpoint()"
        assert tx.subcalls[i]["to"] == gauges[i]
