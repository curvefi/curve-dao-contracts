def test_checkpoint_single(alice, root_gauge, checkpoint_proxy):
    tx = checkpoint_proxy.checkpoint(root_gauge, {"from": alice})

    assert tx.return_value is True

    assert tx.subcalls[0]["function"] == "checkpoint()"
    assert tx.subcalls[0]["to"] == root_gauge
