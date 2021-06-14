import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module")
def param_pool(accounts):
    pool_parameters_mock = """
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
        assert new_price_threshold > new_mid_fee  # dev: price threshold should be higher than the fee
    else:
        new_price_threshold = self.price_threshold
    if new_adjustment_step == MAX_UINT256:
        new_adjustment_step = self.adjustment_step
    assert new_adjustment_step <= new_price_threshold  # dev: adjustment step should be smaller than price threshold

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
    decimals: uint256[8] = [18, 18, 0, 0, 0, 0, 0, 0]
    return decimals

@view
@external
def get_underlying_balances(pool: address) -> uint256[8]:
    # makes the pool appear imbalanced, which we use for testing assymetry checks
    balances: uint256[8] = [10**21, 3 * 10**20, 0, 0, 0, 0, 0, 0]
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


def test_commit_new_fee(accounts, pool_proxy, pool):
    pool_proxy.commit_new_fee(pool, 31337, 42, {"from": accounts[1]})


@pytest.mark.parametrize("idx", range(4))
def test_apply_new_fee(accounts, pool_proxy, pool, idx):
    pool_proxy.commit_new_fee(pool, 31337, 42, {"from": accounts[1]})

    pool_proxy.apply_new_fee(pool, {"from": accounts[idx]})

    assert pool.fee() == 31337
    assert pool.admin_fee() == 42


@pytest.mark.parametrize("idx", [0, 2, 3])
def test_commit_new_fee_no_access(accounts, pool_proxy, pool, idx):
    with brownie.reverts("Access denied"):
        pool_proxy.commit_new_fee(pool, 31337, 42, {"from": accounts[idx]})


def test_ramp_A(accounts, chain, pool_proxy, pool):
    time = chain.time() + 86400 * 2
    pool_proxy.ramp_A(pool, 1000, time, {"from": accounts[1]})

    assert pool.future_A() == 1000
    assert pool.future_A_time() == time


def test_stop_ramp_A(accounts, chain, pool_proxy, pool):
    initial_A = pool.initial_A()

    pool_proxy.ramp_A(pool, 1000, chain.time() + 86400 * 2, {"from": accounts[1]})
    tx = pool_proxy.stop_ramp_A(pool, {"from": accounts[1]})

    assert pool.future_A() == initial_A
    assert pool.future_A_time() == tx.timestamp


@pytest.mark.parametrize("idx", [0, 2, 3])
def test_ramp_A_no_access(accounts, chain, pool_proxy, pool, idx):
    with brownie.reverts("Access denied"):
        pool_proxy.ramp_A(pool, 1000, chain.time() + 86400 * 2, {"from": accounts[idx]})


@pytest.mark.parametrize("idx", [0, 3])
def test_stop_ramp_A_no_access(accounts, pool_proxy, pool, idx):
    with brownie.reverts("Access denied"):
        pool_proxy.stop_ramp_A(pool, {"from": accounts[idx]})


def test_commit_new_parameters(accounts, pool_proxy, param_pool):
    pool_proxy.commit_new_parameters(param_pool, 1000, 31337, 42, 0, {"from": accounts[1]})

    assert param_pool.future_amp() == 1000
    assert param_pool.future_fee() == 31337
    assert param_pool.future_admin_fee() == 42


@pytest.mark.parametrize("idx", [0, 2, 3])
def test_commit_new_parameters_no_access(accounts, pool_proxy, param_pool, idx):
    with brownie.reverts("Access denied"):
        pool_proxy.commit_new_parameters(param_pool, 1000, 0, 0, 0, {"from": accounts[idx]})


def test_commit_new_parameters_not_exist(accounts, pool_proxy, pool):
    with brownie.reverts("dev: if implemented by the pool"):
        pool_proxy.commit_new_parameters(pool, 1000, 0, 0, 0, {"from": accounts[1]})


def test_apply_new_parameters(accounts, pool_proxy, param_pool):
    pool_proxy.commit_new_parameters(param_pool, 1000, 31337, 42, 0, {"from": accounts[1]})
    pool_proxy.apply_new_parameters(param_pool, {"from": accounts[1]})

    assert param_pool.amp() == 1000
    assert param_pool.fee() == 31337
    assert param_pool.admin_fee() == 42


def test_apply_new_parameters_asymmetry_works(accounts, pool_proxy, param_pool):
    # Asymmetry is N * prod(balances) / sum(balances)**N (instead of N**N * ...)
    # bal1 = 10, bal2 = 3, N = 2
    # Pool asymmetry is 0.355 * 1e18
    # min is 0.35 * 1e18
    asym = 2 * (3 * 10) / (3 + 10) ** 2 * 1e18
    pool_proxy.commit_new_parameters(
        param_pool, 1000, 4000000, 0, int(asym * 0.99), {"from": accounts[1]}
    )
    pool_proxy.apply_new_parameters(param_pool, {"from": accounts[1]})


def test_apply_new_parameters_asymmetry_fails(accounts, pool_proxy, param_pool):
    # Pool asymmetry is 0.355 * 1e18
    # min is 0.36 * 1e18
    asym = 2 * (3 * 10) / (3 + 10) ** 2 * 1e18
    pool_proxy.commit_new_parameters(
        param_pool, 1000, 4000000, 0, int(asym * 1.01), {"from": accounts[1]}
    )
    with brownie.reverts("Unsafe to apply"):
        pool_proxy.apply_new_parameters(param_pool, {"from": accounts[1]})


def test_apply_new_parameters_not_exist(accounts, pool_proxy, pool):
    with brownie.reverts("dev: if implemented by the pool"):
        pool_proxy.apply_new_parameters(pool, {"from": accounts[1]})


def test_revert_new_parameters(accounts, pool_proxy, param_pool):
    pool_proxy.commit_new_parameters(param_pool, 1000, 31337, 42, 0, {"from": accounts[1]})
    pool_proxy.revert_new_parameters(param_pool, {"from": accounts[1]})

    assert param_pool.future_amp() == 0
    assert param_pool.future_fee() == 0
    assert param_pool.future_admin_fee() == 0


def test_revert_new_parameters_no_access(accounts, pool_proxy, param_pool):
    with brownie.reverts("Access denied"):
        pool_proxy.revert_new_parameters(param_pool, {"from": accounts[3]})


def test_revert_new_parameters_not_exist(accounts, pool_proxy, pool):
    with brownie.reverts("dev: if implemented by the pool"):
        pool_proxy.revert_new_parameters(ZERO_ADDRESS, {"from": accounts[1]})
