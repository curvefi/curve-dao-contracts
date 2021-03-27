import pytest


@pytest.fixture(scope="module")
def unit_gauge(LiquidityGaugeWrapperUnit, alice, liquidity_gauge, vault):
    contract = LiquidityGaugeWrapperUnit.deploy(
        "Tokenized Gauge", "TG", liquidity_gauge, {"from": alice}
    )
    vault.set_token(contract, {"from": alice})
    yield contract


@pytest.fixture(scope="module")
def vault(UnitVault, accounts):
    deployer = accounts.at("0xf827ac3a510eca8d7f356c9c9d78699d5848cabf", force=True)
    # increment the nonce to our mock vault has the hardcoded address
    for i in range(4):
        deployer.transfer(deployer, 0)

    yield UnitVault.deploy({"from": deployer})
