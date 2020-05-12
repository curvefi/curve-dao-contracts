import pytest


YEAR = 365 * 86400
YEAR_1_SUPPLY = 594661989 * 10 ** 18 // YEAR * YEAR


def approx(a, b, precision=1e-10):
    if a == b == 0:
        return True
    return 2 * abs(a - b) / (a + b) <= precision


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


@pytest.fixture(scope="module")
def block_timestamp(web3):
    def _fn():
        return web3.eth.getBlock(web3.eth.blockNumber)['timestamp']
    yield _fn


@pytest.fixture(scope="module")
def theoretical_supply(rpc, token, block_timestamp):
    def _fn():
        epoch = token.mining_epoch()
        q = 1 / 2 ** .5
        S = 10 ** 9 * 10 ** 18
        if epoch > 0:
            S += int(YEAR_1_SUPPLY * (1 - q ** epoch) / (1 - q))
        S += int(YEAR_1_SUPPLY // YEAR * q ** epoch) * (block_timestamp() - token.start_epoch_time())
        return S

    yield _fn


@pytest.fixture(scope="module")
def token(ERC20CRV, accounts):
    yield ERC20CRV.deploy("Curve DAO Token", "CRV", 18, 10 ** 9, {'from': accounts[0]})


@pytest.fixture(scope="module")
def mock_lp_token(ERC20LP, accounts):  # Not using the actual Curve contract
    yield ERC20LP.deploy("Curve LP token", "usdCrv", 18, 10 ** 9, {'from': accounts[0]})


@pytest.fixture(scope="module")
def gauge_controller(GaugeController, accounts, token):
    yield GaugeController.deploy(token, {'from': accounts[0]})


@pytest.fixture(scope="module")
def liquidity_gauge(LiquidityGauge, accounts, gauge_controller, mock_lp_token, token):
    yield LiquidityGauge.deploy(token, mock_lp_token, gauge_controller, {'from': accounts[0]})


@pytest.fixture(scope="module")
def three_gauges(LiquidityGauge, accounts, gauge_controller, mock_lp_token, token):
    contracts = [
        LiquidityGauge.deploy(token, mock_lp_token, gauge_controller, {'from': accounts[0]})
        for _ in range(3)
    ]

    yield contracts


@pytest.fixture(scope="function")
def minter(Minter, accounts, gauge_controller, token):
    yield Minter.deploy(token, gauge_controller, {'from': accounts[0]})


@pytest.fixture(scope="function")
def voting_escrow(VotingEscrow, accounts, token):
    yield VotingEscrow.deploy(token, {'from': accounts[0]})
