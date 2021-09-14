def test_checkpoint(alice, chain, GaugeController, RootGaugeArbitrum, Minter, interface):
    gauge_controller = GaugeController.at("0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB")
    minter = Minter.at("0xd061D61a4d941c39E5453435B6345Dc261C2fcE0")

    root_gauge = RootGaugeArbitrum.deploy(minter, alice, alice, {"from": alice})
    crv = interface.ERC20(root_gauge.crv_token())

    gauge_controller.add_gauge(root_gauge, 0, 10 ** 18, {"from": gauge_controller.admin()})

    chain.sleep(86400 * 14)

    balance_before = crv.balanceOf("0xa3A7B6F88361F48403514059F1F16C8E78d60EeC")
    root_gauge.checkpoint({"from": alice})
    balance_after = crv.balanceOf("0xa3A7B6F88361F48403514059F1F16C8E78d60EeC")

    assert balance_after > balance_before
