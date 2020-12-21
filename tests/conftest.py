import pytest
from brownie import BTCBurner, CBurner, ETHBurner, LPBurner, MetaBurner, UnderlyingBurner, USDNBurner, YBurner


YEAR = 365 * 86400
INITIAL_RATE = 274_815_283
YEAR_1_SUPPLY = INITIAL_RATE * 10 ** 18 // YEAR * YEAR
INITIAL_SUPPLY = 1_303_030_303


def approx(a, b, precision=1e-10):
    if a == b == 0:
        return True
    return 2 * abs(a - b) / (a + b) <= precision


def pack_values(values):
    packed = b"".join(i.to_bytes(1, "big") for i in values)
    padded = packed + bytes(32 - len(values))
    return padded


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


# helper functions as fixtures

@pytest.fixture(scope="function")
def theoretical_supply(chain, token):
    def _fn():
        epoch = token.mining_epoch()
        q = 1 / 2 ** .25
        S = INITIAL_SUPPLY * 10 ** 18
        if epoch > 0:
            S += int(YEAR_1_SUPPLY * (1 - q ** epoch) / (1 - q))
        S += int(YEAR_1_SUPPLY // YEAR * q ** epoch) * (chain[-1].timestamp - token.start_epoch_time())
        return S

    yield _fn


# account aliases

@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def receiver(accounts):
    yield accounts.at("0x0000000000000000000000000000000000031337", True)


# core contracts

@pytest.fixture(scope="module")
def token(ERC20CRV, accounts):
    yield ERC20CRV.deploy("Curve DAO Token", "CRV", 18, {'from': accounts[0]})


@pytest.fixture(scope="module")
def voting_escrow(VotingEscrow, accounts, token):
    yield VotingEscrow.deploy(token, 'Voting-escrowed CRV', 'veCRV', 'veCRV_0.99', {'from': accounts[0]})


@pytest.fixture(scope="module")
def gauge_controller(GaugeController, accounts, token, voting_escrow):
    yield GaugeController.deploy(token, voting_escrow, {'from': accounts[0]})


@pytest.fixture(scope="module")
def minter(Minter, accounts, gauge_controller, token):
    yield Minter.deploy(token, gauge_controller, {'from': accounts[0]})


@pytest.fixture(scope="module")
def pool_proxy(PoolProxy, accounts):
    yield PoolProxy.deploy(accounts[0], accounts[0], accounts[0], {'from': accounts[0]})


@pytest.fixture(scope="module")
def coin_reward(ERC20, accounts):
    yield ERC20.deploy("YFIIIIII Funance", "YFIIIIII", 18, {'from': accounts[0]})


@pytest.fixture(scope="module")
def reward_contract(CurveRewards, mock_lp_token, accounts, coin_reward):
    contract = CurveRewards.deploy(mock_lp_token, coin_reward, {'from': accounts[0]})
    contract.setRewardDistribution(accounts[0], {'from': accounts[0]})
    yield contract


@pytest.fixture(scope="module")
def liquidity_gauge(LiquidityGauge, accounts, mock_lp_token, minter):
    yield LiquidityGauge.deploy(mock_lp_token, minter, accounts[0], {'from': accounts[0]})


@pytest.fixture(scope="module")
def gauge_v2(LiquidityGaugeV2, alice, mock_lp_token, minter):
    yield LiquidityGaugeV2.deploy("Gauge V2", "G2", mock_lp_token, minter, alice, {'from': alice})


@pytest.fixture(scope="module")
def gauge_wrapper(LiquidityGaugeWrapper, accounts, liquidity_gauge):
    yield LiquidityGaugeWrapper.deploy("Tokenized Gauge", "TG", liquidity_gauge, accounts[0], {'from': accounts[0]})


@pytest.fixture(scope="module")
def liquidity_gauge_reward(LiquidityGaugeReward, accounts, mock_lp_token, minter, reward_contract, coin_reward):
    yield LiquidityGaugeReward.deploy(mock_lp_token, minter, reward_contract, coin_reward, accounts[0], {'from': accounts[0]})


@pytest.fixture(scope="module")
def reward_gauge_wrapper(LiquidityGaugeRewardWrapper, accounts, liquidity_gauge_reward):
    yield LiquidityGaugeRewardWrapper.deploy("Tokenized Reward Gauge", "TG", liquidity_gauge_reward, accounts[0], {'from': accounts[0]})


@pytest.fixture(scope="module")
def three_gauges(LiquidityGauge, accounts, mock_lp_token, minter):
    contracts = [
        LiquidityGauge.deploy(mock_lp_token, minter, accounts[0], {'from': accounts[0]})
        for _ in range(3)
    ]

    yield contracts


# VestingEscrow fixtures

@pytest.fixture(scope="module")
def start_time(chain):
    yield chain.time() + 1000 + 86400*365


@pytest.fixture(scope="module")
def end_time(start_time):
    yield start_time + 100000000


@pytest.fixture(scope="module")
def vesting(VestingEscrow, accounts, coin_a, start_time, end_time):
    contract = VestingEscrow.deploy(coin_a, start_time, end_time, True, accounts[1:5], {'from': accounts[0]})
    coin_a._mint_for_testing(10**21, {'from': accounts[0]})
    coin_a.approve(contract, 10**21, {'from': accounts[0]})
    yield contract


@pytest.fixture(scope="module")
def vesting_target(VestingEscrowSimple, accounts):
    yield VestingEscrowSimple.deploy({'from': accounts[0]})


@pytest.fixture(scope="module")
def vesting_factory(VestingEscrowFactory, accounts, vesting_target):
    yield VestingEscrowFactory.deploy(vesting_target, accounts[0], {'from': accounts[0]})


@pytest.fixture(scope="module")
def vesting_simple(VestingEscrowSimple, accounts, vesting_factory, coin_a, start_time):
    coin_a._mint_for_testing(10**21, {'from': accounts[0]})
    coin_a.transfer(vesting_factory, 10**21, {'from': accounts[0]})
    tx = vesting_factory.deploy_vesting_contract(
        coin_a, accounts[1], 10**20, True, 100000000, start_time, {'from': accounts[0]}
    )
    yield VestingEscrowSimple.at(tx.new_contracts[0])


# parametrized burner fixture

@pytest.fixture(
    scope="module",
    params=[BTCBurner, CBurner, ETHBurner, LPBurner, MetaBurner, UnderlyingBurner, USDNBurner, YBurner]
)
def burner(alice, bob, receiver, pool_proxy, request):
    Burner = request.param
    args = (pool_proxy, receiver, receiver, alice, bob, {'from': alice})
    idx = len(Burner.deploy.abi['inputs']) + 1

    yield Burner.deploy(*args[-idx:])

    # if len(Burner.deploy.abi['inputs']) == 4:
    #     yield Burner.deploy(receiver, receiver, alice, bob, {'from': alice})
    # else:
    #     yield Burner.deploy(receiver, alice, bob, {'from': alice})


# testing contracts

@pytest.fixture(scope="module")
def coin_a(ERC20, accounts):
    yield ERC20.deploy("Coin A", "USDA", 18, {'from': accounts[0]})


@pytest.fixture(scope="module")
def coin_b(ERC20, accounts):
    yield ERC20.deploy("Coin B", "USDB", 18, {'from': accounts[0]})


@pytest.fixture(scope="module")
def mock_lp_token(ERC20LP, accounts):  # Not using the actual Curve contract
    yield ERC20LP.deploy("Curve LP token", "usdCrv", 18, 10 ** 9, {'from': accounts[0]})


@pytest.fixture(scope="module")
def pool(CurvePool, accounts, mock_lp_token, coin_a, coin_b):
    curve_pool = CurvePool.deploy(
        [coin_a, coin_b], mock_lp_token, 100, 4 * 10 ** 6, {'from': accounts[0]}
    )
    mock_lp_token.set_minter(curve_pool, {'from': accounts[0]})

    yield curve_pool


@pytest.fixture(scope="module")
def fee_distributor(FeeDistributor, voting_escrow, accounts, coin_a, chain):
    def f(t=None):
        if not t:
            t = chain.time()
        return FeeDistributor.deploy(voting_escrow, t, coin_a, accounts[0], accounts[0], {'from': accounts[0]})
    yield f
