import pytest
from brownie import (
    ZERO_ADDRESS,
    compile_source,
    convert,
)
from brownie_tokens import ERC20

# YEAR = 365 * 86400
# INITIAL_RATE = 274_815_283
# YEAR_1_SUPPLY = INITIAL_RATE * 10 ** 18 // YEAR * YEAR
# INITIAL_SUPPLY = 1_303_030_303


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


# @pytest.fixture(scope="module")
# def theoretical_supply(chain, token):
#     def _fn():
#         epoch = token.mining_epoch()
#         q = 1 / 2 ** 0.25
#         S = INITIAL_SUPPLY * 10 ** 18
#         if epoch > 0:
#             S += int(YEAR_1_SUPPLY * (1 - q ** epoch) / (1 - q))
#         S += int(YEAR_1_SUPPLY // YEAR * q ** epoch) * (
#             chain[-1].timestamp - token.start_epoch_time()
#         )
#         return S

#     yield _fn


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


# @pytest.fixture(scope="module")
# def token(ERC20CRV, accounts):
#     yield ERC20CRV.deploy("Curve DAO Token", "CRV", 18, {"from": accounts[0]})


@pytest.fixture(scope="module")
def token(ERC20, accounts):
    yield ERC20.deploy("Lixir Token", "LIX", 18, 10000000 * 10 ** 18, {"from": accounts[0]})


@pytest.fixture(scope="module")
def voting_escrow(VotingEscrow, accounts, token):
    yield VotingEscrow.deploy(
        token, "Voting-escrowed CRV", "veCRV", "veCRV_0.99", {"from": accounts[0]}
    )


@pytest.fixture(scope="module")
def gauge_controller(GaugeController, accounts, token, voting_escrow):
    yield GaugeController.deploy(token, voting_escrow, {"from": accounts[0]})


# @pytest.fixture(scope="module")
# def minter(Minter, accounts, gauge_controller, token):
#     yield Minter.deploy(token, gauge_controller, {"from": accounts[0]})


@pytest.fixture(scope="module")
def distributor(LixDistributor, accounts, gauge_controller, token):
    dist = LixDistributor.deploy(token, gauge_controller, accounts[0], {"from": accounts[0]})
    token.approve(dist, 6000000 * 10 ** 18, {"from":accounts[0]})
    dist.set_initial_params(6000000 * 10 ** 18, {"from": accounts[0]})
    yield dist


# @pytest.fixture(scope="module")
# def crypto_pool_proxy(alice, CryptoPoolProxy):
#     return CryptoPoolProxy.deploy(alice, alice, alice, {"from": alice})


# @pytest.fixture(scope="module")
# def pool_proxy(PoolProxy, accounts):
#     yield PoolProxy.deploy(accounts[0], accounts[0], accounts[0], {"from": accounts[0]})


# @pytest.fixture(scope="module")
# def gauge_proxy(GaugeProxy, alice, bob):
#     yield GaugeProxy.deploy(alice, bob, {"from": alice})


# @pytest.fixture(scope="module")
# def coin_reward():
#     yield ERC20("YFIIIIII Funance", "YFIIIIII", 18)


# @pytest.fixture(scope="module")
# def reward_contract(CurveRewards, mock_lp_token, accounts, coin_reward):
#     contract = CurveRewards.deploy(mock_lp_token, coin_reward, {"from": accounts[0]})
#     contract.setRewardDistribution(accounts[0], {"from": accounts[0]})
#     yield contract


# @pytest.fixture(scope="module")
# def liquidity_gauge(LiquidityGauge, accounts, mock_lp_token, minter):
#     yield LiquidityGauge.deploy(mock_lp_token, minter, accounts[0], {"from": accounts[0]})


# @pytest.fixture(scope="module")
# def gauge_v2(LiquidityGaugeV2, alice, mock_lp_token, minter):
#     yield LiquidityGaugeV2.deploy(mock_lp_token, minter, alice, {"from": alice})


# @pytest.fixture(scope="module")
# def gauge_v3(LiquidityGaugeV3, alice, mock_lp_token, minter):
#     yield LiquidityGaugeV3.deploy(mock_lp_token, minter, alice, {"from": alice})


@pytest.fixture(scope="module")
def vault_gauge(VaultGauge, alice, lixir_vault, distributor, accounts, chain):
    yield VaultGauge.deploy(lixir_vault, distributor, alice, {"from": alice})

# @pytest.fixture(scope="module")
# def rewards_only_gauge(RewardsOnlyGauge, alice, mock_lp_token):
#     yield RewardsOnlyGauge.deploy(alice, mock_lp_token, {"from": alice})


# @pytest.fixture(scope="module")
# def gauge_wrapper(LiquidityGaugeWrapper, accounts, liquidity_gauge):
#     yield LiquidityGaugeWrapper.deploy(
#         "Tokenized Gauge", "TG", liquidity_gauge, accounts[0], {"from": accounts[0]}
#     )


# @pytest.fixture(scope="module")
# def liquidity_gauge_reward(
#     LiquidityGaugeReward, accounts, mock_lp_token, minter, reward_contract, coin_reward
# ):
#     yield LiquidityGaugeReward.deploy(
#         mock_lp_token,
#         minter,
#         reward_contract,
#         coin_reward,
#         accounts[0],
#         {"from": accounts[0]},
#     )


# @pytest.fixture(scope="module")
# def reward_gauge_wrapper(LiquidityGaugeRewardWrapper, accounts, liquidity_gauge_reward):
#     yield LiquidityGaugeRewardWrapper.deploy(
#         "Tokenized Reward Gauge",
#         "TG",
#         liquidity_gauge_reward,
#         accounts[0],
#         {"from": accounts[0]},
#     )


@pytest.fixture(scope="module")
def three_gauges(VaultGauge, accounts, lixir_vault, distributor):
    contracts = [
        VaultGauge.deploy(
            lixir_vault,
            distributor,
            accounts[0],
            {"from": accounts[0]}
        )
        for _ in range(3)
    ]

    yield contracts


# VestingEscrow fixtures


# @pytest.fixture(scope="module")
# def start_time(chain):
#     yield chain.time() + 1000 + 86400 * 365


# @pytest.fixture(scope="module")
# def end_time(start_time):
#     yield start_time + 100000000


# @pytest.fixture(scope="module")
# def vesting(VestingEscrow, accounts, coin_a, start_time, end_time):
#     contract = VestingEscrow.deploy(
#         coin_a, start_time, end_time, True, accounts[1:5], {"from": accounts[0]}
#     )
#     coin_a._mint_for_testing(accounts[0], 10 ** 21)
#     coin_a.approve(contract, 10 ** 21, {"from": accounts[0]})
#     yield contract


# @pytest.fixture(scope="module")
# def vesting_target(VestingEscrowSimple, accounts):
#     yield VestingEscrowSimple.deploy({"from": accounts[0]})


# @pytest.fixture(scope="module")
# def vesting_factory(VestingEscrowFactory, accounts, vesting_target):
#     yield VestingEscrowFactory.deploy(vesting_target, accounts[0], {"from": accounts[0]})


# @pytest.fixture(scope="module")
# def vesting_simple(VestingEscrowSimple, accounts, vesting_factory, coin_a, start_time):
#     coin_a._mint_for_testing(vesting_factory, 10 ** 21)
#     tx = vesting_factory.deploy_vesting_contract(
#         coin_a,
#         accounts[1],
#         10 ** 20,
#         True,
#         100000000,
#         start_time,
#         {"from": accounts[0]},
#     )
#     yield VestingEscrowSimple.at(tx.new_contracts[0])


# testing contracts

@pytest.fixture(scope="module")
def local(accounts):
    yield accounts.add('8fa2fdfb89003176a16b707fc860d0881da0d1d8248af210df12d37860996fb2')


@pytest.fixture(scope="module")
def coin_a(ERC20, accounts):
    yield ERC20.deploy("Coin A", "USDA", 18, 0, {"from": accounts[0]})


@pytest.fixture(scope="module")
def coin_b(ERC20, accounts):
    yield ERC20.deploy("Coin A", "USDA", 18, 0, {"from": accounts[0]})


# @pytest.fixture(scope="module")
# def coin_c():
#     yield ERC20("Coin C", "mWBTC", 8)


# @pytest.fixture(scope="module")
# def mock_lp_token(ERC20LP, accounts):  # Not using the actual Curve contract
#     yield ERC20LP.deploy("Curve LP token", "usdCrv", 18, 10 ** 9, {"from": accounts[0]})


# @pytest.fixture(scope="module")
# def pool(CurvePool, accounts, mock_lp_token, coin_a, coin_b):
#     curve_pool = CurvePool.deploy(
#         [coin_a, coin_b], mock_lp_token, 100, 4 * 10 ** 6, {"from": accounts[0]}
#     )
#     mock_lp_token.set_minter(curve_pool, {"from": accounts[0]})

#     yield curve_pool


@pytest.fixture(scope="module")
def registry(LixirRegistry, accounts):
    yield LixirRegistry.deploy(
        accounts[0], accounts[0], accounts[0], accounts[0], {"from": accounts[0]}
    )


@pytest.fixture(scope="module")
def lixir_vault(LixirVault, registry, coin_a, coin_b, accounts):
    vault = LixirVault.deploy(registry, {"from": accounts[0]})
    vault.initialize("Test Vault Token", "LVT", coin_a, coin_b, accounts[0], accounts[0], accounts[0])
    yield vault


@pytest.fixture(scope="module")
def fee_distributor(FeeDistributor, voting_escrow, accounts, coin_a, chain):
    def f(t=None):
        if not t:
            t = chain.time()
        return FeeDistributor.deploy(
            voting_escrow, t, coin_a, accounts[0], accounts[0], {"from": accounts[0]}
        )

    yield f


# @pytest.fixture(scope="module")
# def crypto_coins(coin_a, coin_b, coin_c):
#     return [coin_a, coin_b, coin_c]


# @pytest.fixture(scope="session")
# def crypto_project(pm):
#     return pm("curvefi/curve-crypto-contract@1.0.0")


# @pytest.fixture(scope="module")
# def crypto_lp_token(alice, crypto_project):
#     return crypto_project.CurveTokenV4.deploy("Mock Crypto LP Token", "crvMock", {"from": alice})


# @pytest.fixture(scope="module")
# def crypto_math(alice, crypto_project):
#     return crypto_project.CurveCryptoMath3.deploy({"from": alice})


# @pytest.fixture(scope="module")
# def crypto_views(alice, crypto_project, crypto_math, crypto_coins):
#     source: str = crypto_project.CurveCryptoViews3._build["source"]
#     for idx, coin in enumerate(crypto_coins):
#         new_value = 10 ** (18 - coin.decimals())
#         source = source.replace(f"1,#{idx}", f"{new_value},")
#     Views = compile_source(source, vyper_version="0.2.12").Vyper
#     return Views.deploy(crypto_math, {"from": alice})


# @pytest.fixture(scope="session")
# def crypto_initial_prices():
#     # p = requests.get(
#     #     "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
#     # ).json()
#     # return tuple(int(p[cur]["usd"] * 1e18) for cur in ["bitcoin", "ethereum"])
#     return (39362000000000003670016, 2493090000000000196608)


# @pytest.fixture(scope="module")
# def crypto_pool(
#     alice,
#     crypto_project,
#     crypto_math,
#     crypto_lp_token,
#     crypto_views,
#     crypto_coins,
#     crypto_initial_prices,
# ):
#     # taken from curvefi/curve-crypto-contract
#     keys = [0, 1, 2, 16, 17, 18, "1,#0", "1,#1", "1,#2"]
#     values = (
#         [crypto_math.address, crypto_lp_token.address, crypto_views.address]
#         + [coin.address for coin in crypto_coins]
#         + [f"{10 ** (18 - coin.decimals())}," for coin in crypto_coins]
#     )
#     source = crypto_project.CurveCryptoSwap._build["source"]
#     for k, v in zip(keys, values):
#         if isinstance(k, int):
#             k = convert.to_address(convert.to_bytes(k, "bytes20"))
#         source.replace(k, v)

#     CryptoPool = compile_source(source, vyper_version="0.2.12").Vyper
#     swap = CryptoPool.deploy(
#         alice,
#         135 * 3 ** 3,  # A
#         int(7e-5 * 1e18),  # gamma
#         int(4e-4 * 1e10),  # mid_fee
#         int(4e-3 * 1e10),  # out_fee
#         int(0.0028 * 1e18),  # price_threshold
#         int(0.01 * 1e18),  # fee_gamma
#         int(0.0015 * 1e18),  # adjustment_step
#         0,  # admin_fee
#         600,  # ma_half_time
#         crypto_initial_prices,
#         {"from": alice},
#     )
#     crypto_lp_token.set_minter(swap, {"from": alice})
#     return swap
