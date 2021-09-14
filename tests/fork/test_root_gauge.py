import brownie
import pytest


@pytest.fixture(scope="module")
def root_gauge(GaugeController, Minter, RootGaugeArbitrum, alice, chain):
    gauge_controller = GaugeController.at("0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB")
    minter = Minter.at("0xd061D61a4d941c39E5453435B6345Dc261C2fcE0")

    root_gauge = RootGaugeArbitrum.deploy(
        minter, alice, 1000000, 990000000, 10000000000000, {"from": alice}
    )

    gauge_controller.add_gauge(root_gauge, 0, 10 ** 18, {"from": gauge_controller.admin()})

    chain.mine(timedelta=86400 * 14)
    return root_gauge


def test_checkpoint(alice, interface, root_gauge):
    crv = interface.ERC20(root_gauge.crv_token())

    balance_before = crv.balanceOf("0xa3A7B6F88361F48403514059F1F16C8E78d60EeC")
    root_gauge.checkpoint({"from": alice, "value": "0.001 ether"})
    balance_after = crv.balanceOf("0xa3A7B6F88361F48403514059F1F16C8E78d60EeC")

    assert balance_after > balance_before


def test_insufficient_ether(alice, root_gauge):
    with brownie.reverts():
        root_gauge.checkpoint({"from": alice, "value": "0.0009 ether"})


def test_excess_ether(alice, root_gauge):
    root_gauge.checkpoint({"from": alice, "value": "0.00123 ether"})
    assert root_gauge.balance() == "0.00023 ether"


def test_excess_ether_multiple_checkpoints(alice, root_gauge, chain):
    root_gauge.checkpoint({"from": alice, "value": "0.0035 ether"})
    chain.sleep(86400 * 7)
    root_gauge.checkpoint({"from": alice})
    assert root_gauge.balance() == "0.0015 ether"


def test_modify_gas(alice, root_gauge):
    root_gauge.set_arbitrum_fees(2000000, 50000000, 66000000000000, {"from": alice})
    assert root_gauge.get_total_bridge_cost() == 2000000 * 50000000 + 66000000000000

    root_gauge.checkpoint({"from": alice, "value": 2000000 * 50000000 + 66000000000000})
    assert root_gauge.balance() == 0


def test_modify_gas_is_guarded(bob, root_gauge):
    with brownie.reverts():
        root_gauge.set_arbitrum_fees(2000000, 50000000, 66000000000000, {"from": bob})
