import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
DAY = 86400


@pytest.fixture(scope="module")
def param_pool(accounts):
    pool_parameters_mock = """
# @version 0.2.12

A_MULTIPLIER: constant(uint256) = 100
ADMIN_ACTIONS_DELAY: constant(uint256) = 3 * 86400
MIN_RAMP_TIME: constant(uint256) = 86400
MAX_ADMIN_FEE: constant(uint256) = 10 * 10 ** 9
MIN_FEE: constant(uint256) = 5 * 10 ** 5  # 0.5 bps
MAX_FEE: constant(uint256) = 5 * 10 ** 9
MAX_A: constant(uint256) = 10000 * A_MULTIPLIER
MAX_A_CHANGE: constant(uint256) = 10
MIN_GAMMA: constant(uint256) = 10**10
MAX_GAMMA: constant(uint256) = 10**16

admin_actions_deadline: public(uint256)
initial_A_gamma: public(uint256)
future_A_gamma: public(uint256)
initial_A_gamma_time: public(uint256)
future_A_gamma_time: public(uint256)
price_threshold: public(uint256)
future_price_threshoold: public(uint256)
fee_gamma: public(uint256)
future_fee_gamma: public(uint256)
adjustment_step: public(uint256)
future_adjustment_step: public(uint256)
ma_half_time: public(uint256)
future_ma_half_time: public(uint256)
mid_fee: public(uint256)
out_fee: public(uint256)
admin_fee: public(uint256)
future_mid_fee: public(uint256)
future_out_fee: public(uint256)
future_admin_fee: public(uint256)


@view
@internal
def _A_gamma() -> (uint256, uint256):
    t1: uint256 = self.future_A_gamma_time

    A_gamma_1: uint256 = self.future_A_gamma
    gamma1: uint256 = bitwise_and(A_gamma_1, 2**128-1)
    A1: uint256 = shift(A_gamma_1, -128)

    if block.timestamp < t1:
        # handle ramping up and down of A
        A_gamma_0: uint256 = self.initial_A_gamma
        t0: uint256 = self.initial_A_gamma_time

        # Less readable but more compact way of writing and converting to uint256
        # gamma0: uint256 = bitwise_and(A_gamma_0, 2**128-1)
        # A0: uint256 = shift(A_gamma_0, -128)
        # A1 = A0 + (A1 - A0) * (block.timestamp - t0) / (t1 - t0)
        # gamma1 = gamma0 + (gamma1 - gamma0) * (block.timestamp - t0) / (t1 - t0)

        t1 -= t0
        t0 = block.timestamp - t0

        A1 = (shift(A_gamma_0, -128) * (t1 - t0) + A1 * t0) / t1
        gamma1 = (bitwise_and(A_gamma_0, 2**128-1) * (t1 - t0) + gamma1 * t0) / t1

    return A1, gamma1

@external
@pure
def price_oracle(k: uint256) -> uint256:
    prices: uint256[2] = [2 * 10 ** 18, 4 * 10 ** 18]
    return prices[k]

@external
def ramp_A_gamma(future_A: uint256, future_gamma: uint256, future_time: uint256):
    assert block.timestamp > self.initial_A_gamma_time + (MIN_RAMP_TIME-1)
    assert future_time > block.timestamp + (MIN_RAMP_TIME-1)  # dev: insufficient time

    initial_A: uint256 = 0
    initial_gamma: uint256 = 0
    initial_A, initial_gamma = self._A_gamma()
    initial_A_gamma: uint256 = shift(initial_A, 128)
    initial_A_gamma = bitwise_or(initial_A_gamma, initial_gamma)

    future_A_p: uint256 = future_A * A_MULTIPLIER

    assert future_A > 0
    assert future_A < MAX_A
    assert future_gamma > MIN_GAMMA-1
    assert future_gamma < MAX_GAMMA+1
    if future_A_p < initial_A:
        assert future_A_p * MAX_A_CHANGE >= initial_A
    else:
        assert future_A_p <= initial_A * MAX_A_CHANGE

    self.initial_A_gamma = initial_A_gamma
    self.initial_A_gamma_time = block.timestamp

    future_A_gamma: uint256 = shift(future_A_p, 128)
    future_A_gamma = bitwise_or(future_A_gamma, future_gamma)
    self.future_A_gamma_time = future_time
    self.future_A_gamma = future_A_gamma

@external
def stop_ramp_A_gamma():
    current_A: uint256 = 0
    current_gamma: uint256 = 0
    current_A, current_gamma = self._A_gamma()
    current_A_gamma: uint256 = shift(current_A, 128)
    current_A_gamma = bitwise_or(current_A_gamma, current_gamma)
    self.initial_A_gamma = current_A_gamma
    self.future_A_gamma = current_A_gamma
    self.initial_A_gamma_time = block.timestamp
    self.future_A_gamma_time = block.timestamp
    # now (block.timestamp < t1) is always False, so we return saved A

@external
def commit_new_parameters(
    _new_mid_fee: uint256,
    _new_out_fee: uint256,
    _new_admin_fee: uint256,
    _new_fee_gamma: uint256,
    _new_price_threshold: uint256,
    _new_adjustment_step: uint256,
    _new_ma_half_time: uint256,
    ):
    assert self.admin_actions_deadline == 0  # dev: active action

    new_mid_fee: uint256 = _new_mid_fee
    new_out_fee: uint256 = _new_out_fee
    new_admin_fee: uint256 = _new_admin_fee
    new_fee_gamma: uint256 = _new_fee_gamma
    new_price_threshold: uint256 = _new_price_threshold
    new_adjustment_step: uint256 = _new_adjustment_step
    new_ma_half_time: uint256 = _new_ma_half_time

    # Fees
    if new_out_fee != MAX_UINT256:
        assert new_out_fee < MAX_FEE+1  # dev: fee is out of range
        assert new_out_fee > MIN_FEE-1  # dev: fee is out of range
    else:
        new_out_fee = self.out_fee
    if new_mid_fee == MAX_UINT256:
        new_mid_fee = self.mid_fee
    assert new_mid_fee <= new_out_fee  # dev: mid-fee is too high
    if new_admin_fee != MAX_UINT256:
        assert new_admin_fee < MAX_ADMIN_FEE+1  # dev: admin fee exceeds maximum
    else:
        new_admin_fee = self.admin_fee

    # AMM parameters
    if new_fee_gamma != MAX_UINT256:
        assert new_fee_gamma > 0  # dev: fee_gamma out of range [1 .. 2**100]
        assert new_fee_gamma < 2**100  # dev: fee_gamma out of range [1 .. 2**100]
    else:
        new_fee_gamma = self.fee_gamma
    if new_price_threshold != MAX_UINT256:
        assert new_price_threshold > new_mid_fee
    else:
        new_price_threshold = self.price_threshold
    if new_adjustment_step == MAX_UINT256:
        new_adjustment_step = self.adjustment_step
    assert new_adjustment_step <= new_price_threshold

    # MA
    if new_ma_half_time != MAX_UINT256:
        assert new_ma_half_time > 0  # dev: MA time should be shorter than 1 week
        assert new_ma_half_time < 7*86400  # dev: MA time should be shorter than 1 week
    else:
        new_ma_half_time = self.ma_half_time

    _deadline: uint256 = block.timestamp + ADMIN_ACTIONS_DELAY
    self.admin_actions_deadline = _deadline

    self.future_admin_fee = new_admin_fee
    self.future_mid_fee = new_mid_fee
    self.future_out_fee = new_out_fee
    self.future_fee_gamma = new_fee_gamma
    self.future_price_threshoold = new_price_threshold
    self.future_adjustment_step = new_adjustment_step
    self.future_ma_half_time = new_ma_half_time

@external
@nonreentrant('lock')
def apply_new_parameters():
    assert block.timestamp >= self.admin_actions_deadline  # dev: insufficient time
    assert self.admin_actions_deadline != 0  # dev: no active action

    self.admin_actions_deadline = 0

    admin_fee: uint256 = self.future_admin_fee
    self.admin_fee = admin_fee
    mid_fee: uint256 = self.future_mid_fee
    self.mid_fee = mid_fee
    out_fee: uint256 = self.future_out_fee
    self.out_fee = out_fee
    fee_gamma: uint256 = self.future_fee_gamma
    self.fee_gamma = fee_gamma
    price_threshold: uint256 = self.future_price_threshoold
    self.price_threshold = price_threshold
    adjustment_step: uint256 = self.future_adjustment_step
    self.adjustment_step = adjustment_step
    ma_half_time: uint256 = self.future_ma_half_time
    self.ma_half_time = ma_half_time

@external
def revert_new_parameters():
    self.admin_actions_deadline = 0
    """
    yield brownie.compile_source(pool_parameters_mock).Vyper.deploy({"from": accounts[0]})


@pytest.fixture(scope="module")
def registry(accounts):
    registry_mock = """
# @version 0.2.7

@view
@external
def get_decimals(pool: address) -> uint256[8]:
    decimals: uint256[8] = [18, 18, 8, 0, 0, 0, 0, 0]
    return decimals

@view
@external
def get_underlying_balances(pool: address) -> uint256[8]:
    # makes the pool appear imbalanced, which we use for testing assymetry checks
    balances: uint256[8] = [10**21, 5*10**20, 5*10**10, 0, 0, 0, 0, 0]
    return balances
    """
    yield brownie.compile_source(registry_mock).Vyper.deploy({"from": accounts[0]})


@pytest.fixture(scope="module", autouse=True)
def provider(registry):
    provider_mock = f"""
# @version 0.2.7
@view
@external
def get_registry() -> address:
    return {registry.address}
    """
    yield brownie.compile_source(provider_mock).Vyper.deploy(
        {"from": "0x07A3458AD662FBCDD4FcA0b1b37BE6A5b1Bcd7ac"}
    )


@pytest.fixture
def new_params():
    return [
        int(4e-3 * 1e10),  # new mid fee
        int(4e-2 * 1e10),  # new out fee
        400000,  # new admin fee
        int(0.02 * 1e18),  # new fee gamma
        int(0.003 * 1e18),  # new price threshold
        int(0.003 * 1e18),  # new adjustment step
        400,  # new ma half time
    ]


def test_ramp_A_gamma(accounts, chain, crypto_pool_proxy, crypto_pool):
    time = chain.time() + 86400 * 2
    future_A = 130 * 3 ** 3
    future_gamma = 7 * 10 ** 14
    crypto_pool_proxy.ramp_A_gamma(crypto_pool, future_A, future_gamma, time, {"from": accounts[1]})

    chain.mine(timestamp=time + DAY)

    assert crypto_pool.A() == future_A
    assert crypto_pool.gamma() == future_gamma
    assert crypto_pool.future_A_gamma_time() == time


def test_stop_ramp_A_gamma(accounts, chain, crypto_pool_proxy, crypto_pool):
    time = chain.time() + 86400 * 2
    future_A = 130 * 3 ** 3
    future_gamma = 7 * 10 ** 14
    crypto_pool_proxy.ramp_A_gamma(crypto_pool, future_A, future_gamma, time, {"from": accounts[1]})

    tx = crypto_pool_proxy.stop_ramp_A_gamma(crypto_pool, {"from": accounts[1]})
    chain.sleep(DAY * 3)

    assert crypto_pool.A() != future_A
    assert crypto_pool.gamma() != future_gamma
    assert crypto_pool.future_A_gamma_time() == tx.timestamp


@pytest.mark.parametrize("idx", [0, 2, 3])
def test_ramp_A_gamma_no_access(accounts, chain, crypto_pool_proxy, crypto_pool, idx):
    time = chain.time() + 86400 * 2
    future_A = 130 * 3 ** 3
    future_gamma = 7 * 10 ** 14
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.ramp_A_gamma(
            crypto_pool, future_A, future_gamma, time, {"from": accounts[idx]}
        )


@pytest.mark.parametrize("idx", [0, 3])
def test_stop_ramp_A_gamma_no_access(accounts, crypto_pool_proxy, crypto_pool, idx):
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.stop_ramp_A_gamma(crypto_pool, {"from": accounts[idx]})


def test_commit_new_parameters(accounts, crypto_pool_proxy, param_pool, new_params):
    crypto_pool_proxy.commit_new_parameters(param_pool, *new_params, {"from": accounts[1]})

    fns = [
        "future_mid_fee",
        "future_out_fee",
        "future_admin_fee",
        "future_fee_gamma",
        "future_price_threshoold",
        "future_adjustment_step",
        "future_ma_half_time",
    ]

    for idx, fn in enumerate(fns):
        assert getattr(param_pool, fn)() == new_params[idx]


@pytest.mark.parametrize("idx", [0, 2, 3])
def test_commit_new_parameters_no_access(accounts, crypto_pool_proxy, param_pool, idx, new_params):
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.commit_new_parameters(param_pool, *new_params, {"from": accounts[idx]})


def test_commit_new_parameters_not_exist(accounts, crypto_pool_proxy, new_params):
    with brownie.reverts("dev: if implemented by the pool"):
        crypto_pool_proxy.commit_new_parameters(ZERO_ADDRESS, *new_params, {"from": accounts[1]})


def test_apply_new_parameters(accounts, chain, crypto_pool_proxy, param_pool, new_params):
    crypto_pool_proxy.commit_new_parameters(param_pool, *new_params, {"from": accounts[1]})
    chain.sleep(DAY * 3)
    crypto_pool_proxy.apply_new_parameters(param_pool, {"from": accounts[1]})

    fns = [
        "mid_fee",
        "out_fee",
        "admin_fee",
        "fee_gamma",
        "price_threshold",
        "adjustment_step",
        "ma_half_time",
    ]

    for idx, fn in enumerate(fns):
        assert getattr(param_pool, fn)() == new_params[idx]


def test_apply_new_parameters_not_exist(accounts, crypto_pool_proxy):
    with brownie.reverts("dev: if implemented by the pool"):
        crypto_pool_proxy.apply_new_parameters(ZERO_ADDRESS, {"from": accounts[1]})


def test_revert_new_parameters(accounts, crypto_pool_proxy, param_pool, new_params):
    crypto_pool_proxy.commit_new_parameters(param_pool, *new_params, {"from": accounts[1]})
    crypto_pool_proxy.revert_new_parameters(param_pool, {"from": accounts[1]})

    fns = [
        "future_mid_fee",
        "future_out_fee",
        "future_admin_fee",
        "future_fee_gamma",
        "future_price_threshoold",
        "future_adjustment_step",
        "future_ma_half_time",
    ]

    # prevents new parameters from being applied
    assert param_pool.admin_actions_deadline() == 0
    for idx, fn in enumerate(fns):
        assert getattr(param_pool, fn)() == new_params[idx]


def test_revert_new_parameters_no_access(accounts, crypto_pool_proxy, param_pool):
    with brownie.reverts("Access denied"):
        crypto_pool_proxy.revert_new_parameters(param_pool, {"from": accounts[3]})


def test_revert_new_parameters_not_exist(accounts, crypto_pool_proxy):
    with brownie.reverts("dev: if implemented by the pool"):
        crypto_pool_proxy.revert_new_parameters(ZERO_ADDRESS, {"from": accounts[1]})
