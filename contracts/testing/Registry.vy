# @version 0.1.0b17
# This is an old registry which will be used for those contracts which are affected by the sudden-change issue

MAX_COINS: constant(int128) = 8

ZA: constant(address) = ZERO_ADDRESS
EMPTY_ADDRESS_ARRAY: constant(address[MAX_COINS]) = [ZA, ZA, ZA, ZA, ZA, ZA, ZA, ZA]

ZERO: constant(uint256) = convert(0, uint256)
EMPTY_UINT256_ARRAY: constant(uint256[MAX_COINS]) = [ZERO, ZERO, ZERO, ZERO, ZERO, ZERO, ZERO, ZERO]

CALC_INPUT_SIZE: constant(int128) = 100


struct PoolArray:
    location: uint256
    decimals: bytes32
    underlying_decimals: bytes32
    rate_method_id: bytes32
    lp_token: address
    coins: address[MAX_COINS]
    ul_coins: address[MAX_COINS]
    calculator: address

struct PoolCoins:
    coins: address[MAX_COINS]
    underlying_coins: address[MAX_COINS]
    decimals: uint256[MAX_COINS]
    underlying_decimals: uint256[MAX_COINS]

struct PoolInfo:
    balances: uint256[MAX_COINS]
    underlying_balances: uint256[MAX_COINS]
    decimals: uint256[MAX_COINS]
    underlying_decimals: uint256[MAX_COINS]
    lp_token: address
    A: uint256
    fee: uint256


contract ERC20:
    def decimals() -> uint256: constant
    def balanceOf(addr: address) -> uint256: constant
    def approve(spender: address, amount: uint256) -> bool: modifying
    def transfer(to: address, amount: uint256) -> bool: modifying
    def transferFrom(spender: address, to: address, amount: uint256) -> bool: modifying

contract CurvePool:
    def A() -> uint256: constant
    def fee() -> uint256: constant
    def coins(i: int128) -> address: constant
    def underlying_coins(i: int128) -> address: constant
    def get_dy(i: int128, j: int128, dx: uint256) -> uint256: constant
    def get_dy_underlying(i: int128, j: int128, dx: uint256) -> uint256: constant
    def exchange(i: int128, j: int128, dx: uint256, min_dy: uint256): modifying
    def exchange_underlying(i: int128, j: int128, dx: uint256, min_dy: uint256): modifying

contract GasEstimator:
    def estimate_gas_used(_pool: address, _from: address, _to: address) -> uint256: constant

contract Calculator:
    def get_dx(n_coins: int128, balances: uint256[MAX_COINS], amp: uint256, fee: uint256,
               rates: uint256[MAX_COINS], precisions: uint256[MAX_COINS], underlying: bool,
               i: int128, j: int128, dx: uint256) -> uint256: constant
    def get_dy(n_coins: int128, balances: uint256[MAX_COINS], amp: uint256, fee: uint256,
               rates: uint256[MAX_COINS], precisions: uint256[MAX_COINS], underlying: bool,
               i: int128, j: int128, dx: uint256[CALC_INPUT_SIZE]) -> uint256[CALC_INPUT_SIZE]: constant


CommitNewAdmin: event({deadline: indexed(uint256), admin: indexed(address)})
NewAdmin: event({admin: indexed(address)})
TokenExchange: event({
    buyer: indexed(address),
    pool: indexed(address),
    token_sold: address,
    token_bought: address,
    amount_sold: uint256,
    amount_bought: uint256
})
PoolAdded: event({pool: indexed(address), rate_method_id: bytes[4]})
PoolRemoved: event({pool: indexed(address)})


admin: public(address)
transfer_ownership_deadline: uint256
future_admin: address

pool_list: public(address[65536])   # master list of pools
pool_count: public(uint256)         # actual length of pool_list

pool_data: map(address, PoolArray)
returns_none: map(address, bool)

# mapping of estimated gas costs for pools and coins
# for a pool the values are [wrapped exchange, underlying exchange]
# for a coin the values are [transfer cost, 0]
gas_estimate_values: map(address, uint256[2])

# pool -> gas estimation contract
# used when gas costs for a pool are too complex to be handled by summing
# values in `gas_estimate_values`
gas_estimate_contracts: map(address, address)

# mapping of coin -> coin -> pools for trading
# all addresses are converted to uint256 prior to storage. coin addresses are stored
# using the smaller value first. within each pool address array, the first value
# is shifted 16 bits to the left, and these 16 bits are used to store the array length.

markets: map(uint256, map(uint256, uint256[65536]))


@public
def __init__(_returns_none: address[4]):
    """
    @notice Constructor function
    @param _returns_none Token addresses that return None on a successful transfer
    """
    self.admin = msg.sender
    for _addr in _returns_none:
        if _addr == ZERO_ADDRESS:
            break
        self.returns_none[_addr] = True


@public
@payable
def __default__():
    pass


@public
@constant
def find_pool_for_coins(_from: address, _to: address, i: uint256 = 0) -> address:
    """
    @notice Find an available pool for exchanging two coins
    @dev For coins where there is no underlying coin, or where
         the underlying coin cannot be swapped, the rate is
         given as 1e18
    @param _from Address of coin to be sent
    @param _to Address of coin to be received
    @param i Index value. When multiple pools are available
            this value is used to return the n'th address.
    @return Pool address
    """

    _first: uint256 = min(convert(_from, uint256), convert(_to, uint256))
    _second: uint256 = max(convert(_from, uint256), convert(_to, uint256))

    if i == 0:
        _addr: uint256 = shift(self.markets[_first][_second][0], -16)
        return convert(convert(_addr, bytes32), address)

    return convert(convert(self.markets[_first][_second][i], bytes32), address)


@public
@constant
def get_pool_coins(_pool: address) -> PoolCoins:
    """
    @notice Get information on coins in a pool
    @dev Empty values in the returned arrays may be ignored
    @param _pool Pool address
    @return Coin addresses, underlying coin addresses, underlying coin decimals
    """
    _coins: PoolCoins = PoolCoins({
        coins: EMPTY_ADDRESS_ARRAY,
        underlying_coins: EMPTY_ADDRESS_ARRAY,
        decimals: EMPTY_UINT256_ARRAY,
        underlying_decimals: EMPTY_UINT256_ARRAY,
    })
    _decimals_packed: bytes32 = self.pool_data[_pool].decimals
    _udecimals_packed: bytes32 = self.pool_data[_pool].underlying_decimals

    for i in range(MAX_COINS):
        _coins.coins[i] = self.pool_data[_pool].coins[i]
        if _coins.coins[i] == ZERO_ADDRESS:
            break
        _coins.underlying_coins[i] = self.pool_data[_pool].ul_coins[i]
        _coins.decimals[i] = convert(slice(_decimals_packed, i, 1), uint256)
        _coins.underlying_decimals[i] = convert(slice(_udecimals_packed, i, 1), uint256)

    return _coins


@public
def get_pool_info(_pool: address) -> PoolInfo:
    """
    @notice Get information on a pool
    @dev Reverts if the pool address is unknown
    @param _pool Pool address
    @return balances, underlying balances, decimals, underlying decimals,
            lp token, amplification coefficient, fees
    """
    _pool_info: PoolInfo = PoolInfo({
        balances: EMPTY_UINT256_ARRAY,
        underlying_balances: EMPTY_UINT256_ARRAY,
        decimals: EMPTY_UINT256_ARRAY,
        underlying_decimals: EMPTY_UINT256_ARRAY,
        lp_token: self.pool_data[_pool].lp_token,
        A: CurvePool(_pool).A(),
        fee: CurvePool(_pool).fee()
    })

    _rate_method_id: bytes[4] = slice(self.pool_data[_pool].rate_method_id, 0, 4)
    _decimals_packed: bytes32 = self.pool_data[_pool].decimals
    _udecimals_packed: bytes32 = self.pool_data[_pool].underlying_decimals

    for i in range(MAX_COINS):
        _coin: address = self.pool_data[_pool].coins[i]
        if _coin == ZERO_ADDRESS:
            assert i != 0
            break

        _pool_info.decimals[i] = convert(slice(_decimals_packed, i, 1), uint256)
        _pool_info.underlying_decimals[i] = convert(slice(_udecimals_packed, i, 1), uint256)

        if _coin == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
            _pool_info.balances[i] = as_unitless_number(self.balance)
        else:
            _pool_info.balances[i] = ERC20(_coin).balanceOf(_pool)

        _underlying_coin: address = self.pool_data[_pool].ul_coins[i]
        if _coin == _underlying_coin:
            _pool_info.underlying_balances[i] = _pool_info.balances[i]
        elif _underlying_coin == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
            _pool_info.underlying_balances[i] = as_unitless_number(self.balance)
        elif _underlying_coin != ZERO_ADDRESS:
            _response: bytes[32] = raw_call(_coin, _rate_method_id, outsize=32)  # dev: bad response
            _rate: uint256 = convert(_response, uint256)
            _pool_info.underlying_balances[i] = _pool_info.balances[i] * _rate / 10 ** 18

    return _pool_info


@public
def get_pool_rates(_pool: address) -> uint256[MAX_COINS]:
    """
    @notice Get rates between coins and underlying coins
    @dev For coins where there is no underlying coin, or where
         the underlying coin cannot be swapped, the rate is
         given as 1e18
    @param _pool Pool address
    @return Rates between coins and underlying coins
    """
    _rates: uint256[MAX_COINS] = EMPTY_UINT256_ARRAY
    _rate_method_id: bytes[4] = slice(self.pool_data[_pool].rate_method_id, 0, 4)
    for i in range(MAX_COINS):
        _coin: address = self.pool_data[_pool].coins[i]
        if _coin == ZERO_ADDRESS:
            break
        if _coin == self.pool_data[_pool].ul_coins[i]:
            _rates[i] = 10 ** 18
        else:
            _response: bytes[32] = raw_call(_coin, _rate_method_id, outsize=32)  # dev: bad response
            _rates[i] = convert(_response, uint256)

    return _rates


@private
@constant
def _get_token_indices(
    _pool: address,
    _from: address,
    _to: address
) -> (int128, int128, bool):
    """
    Convert coin addresses to indices for use with pool methods.
    """
    i: int128 = -1
    j: int128 = -1
    _coin: address = ZERO_ADDRESS
    _check_underlying: bool = True

    # check coin markets
    for x in range(MAX_COINS):
        _coin = self.pool_data[_pool].coins[x]
        if _coin == _from:
            i = x
        elif _coin == _to:
            j = x
        elif _coin == ZERO_ADDRESS:
            break
        else:
            continue
        if min(i, j) > -1:
            return i, j, False
        if _coin != self.pool_data[_pool].ul_coins[x]:
            _check_underlying = False

    assert _check_underlying, "No available market"

    # check underlying coin markets
    for x in range(MAX_COINS):
        _coin = self.pool_data[_pool].ul_coins[x]
        if _coin == _from:
            i = x
        elif _coin == _to:
            j = x
        elif _coin == ZERO_ADDRESS:
            break
        else:
            continue
        if min(i, j) > -1:
            return i, j, True

    raise "No available market"


@public
@constant
def estimate_gas_used(_pool: address, _from: address, _to: address) -> uint256:
    """
    @notice Estimate the gas used in an exchange.
    @param _pool Pool address
    @param _from Address of coin to be sent
    @param _to Address of coin to be received
    @return Upper-bound gas estimate, in wei
    """
    _estimator: address = self.gas_estimate_contracts[_pool]
    if _estimator != ZERO_ADDRESS:
        return GasEstimator(_estimator).estimate_gas_used(_pool, _from, _to)

    # here we call `_get_token_indices` to find out if the exchange involves
    # wrapped or underlying coins, and convert the result to an integer that we
    # use as an index for `gas_estimate_values`
    # 0 == wrapped   1 == underlying
    _idx_underlying: int128 = convert(
        self._get_token_indices(_pool, _from, _to)[2],
        int128
    )

    _total: uint256 = self.gas_estimate_values[_pool][_idx_underlying]
    assert _total != 0  # dev: pool value not set

    for _addr in [_from, _to]:
        _gas: uint256 = self.gas_estimate_values[_addr][0]
        assert _gas != 0  # dev: coin value not set
        _total += _gas

    return _total


@public
@constant
def get_exchange_amount(
    _pool: address,
    _from: address,
    _to: address,
    _amount: uint256
) -> uint256:
    """
    @notice Get the current number of coins received in an exchange
    @param _pool Pool address
    @param _from Address of coin to be sent
    @param _to Address of coin to be received
    @param _amount Quantity of `_from` to be sent
    @return Quantity of `_to` to be received
    """
    i: int128 = 0
    j: int128 = 0
    _is_underlying: bool = False
    i, j, _is_underlying = self._get_token_indices(_pool, _from, _to)

    if _is_underlying:
        return CurvePool(_pool).get_dy_underlying(i, j, _amount)
    else:
        return CurvePool(_pool).get_dy(i, j, _amount)


@public
@payable
@nonreentrant("lock")
def exchange(
    _pool: address,
    _from: address,
    _to: address,
    _amount: uint256,
    _expected: uint256
) -> bool:
    """
    @notice Perform an exchange.
    @dev Prior to calling this function you must approve
         this contract to transfer `_amount` coins from `_from`
    @param _from Address of coin being sent
    @param _to Address of coin being received
    @param _amount Quantity of `_from` being sent
    @param _expected Minimum quantity of `_from` received
           in order for the transaction to succeed
    @return True
    """
    i: int128 = 0
    j: int128 = 0
    _is_underlying: bool = False
    i, j, _is_underlying = self._get_token_indices(_pool, _from, _to)

    # record initial balance
    _initial_balance: uint256 = 0
    if _to == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        _initial_balance = as_unitless_number(self.balance - msg.value)
    else:
        _initial_balance = ERC20(_to).balanceOf(self)

    # perform / verify input transfer
    if _from == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        assert _amount == msg.value, "Incorrect ETH amount"
    elif self.returns_none[_from]:
        ERC20(_from).transferFrom(msg.sender, self, _amount)
    else:
        assert_modifiable(ERC20(_from).transferFrom(msg.sender, self, _amount))

    # perform coin exchange
    if _is_underlying:
        CurvePool(_pool).exchange_underlying(i, j, _amount, _expected, value=msg.value)
    else:
        CurvePool(_pool).exchange(i, j, _amount, _expected, value=msg.value)

    # perform output transfer
    _received: uint256 = 0
    if _to == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        _received = as_unitless_number(self.balance) - _initial_balance
        send(msg.sender, _received)
    else:
        _received = ERC20(_to).balanceOf(self) - _initial_balance
        if self.returns_none[_to]:
            ERC20(_to).transfer(msg.sender, _received)
        else:
            assert_modifiable(ERC20(_to).transfer(msg.sender, _received))

    log.TokenExchange(msg.sender, _pool, _from, _to, _amount, _received)

    return True


@public
def get_input_amount(_pool: address, _from: address, _to: address, _amount: uint256) -> uint256:
    """
    @notice Get the current number of coins required to receive the given amount in an exchange
    @param _pool Pool address
    @param _from Address of coin to be sent
    @param _to Address of coin to be received
    @param _amount Quantity of `_to` to be received
    @return Quantity of `_from` to be sent
    """
    i: int128 = 0
    j: int128 = 0
    _is_underlying: bool = False
    i, j, _is_underlying = self._get_token_indices(_pool, _from, _to)

    _amp: uint256 = CurvePool(_pool).A()
    _fee: uint256 = CurvePool(_pool).fee()

    _decimals_packed: bytes32 = EMPTY_BYTES32
    if _is_underlying:
        _decimals_packed = self.pool_data[_pool].underlying_decimals
    else:
        _decimals_packed = self.pool_data[_pool].decimals

    _rates: uint256[MAX_COINS] = EMPTY_UINT256_ARRAY
    _balances: uint256[MAX_COINS] = EMPTY_UINT256_ARRAY
    _precisions: uint256[MAX_COINS] = EMPTY_UINT256_ARRAY
    _n_coins: int128 = 0
    _coin: address = ZERO_ADDRESS
    for x in range(MAX_COINS):
        _coin = self.pool_data[_pool].coins[x]

        if _coin == ZERO_ADDRESS:
            _n_coins = x
            break

        if _coin == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
            _balances[x] = as_unitless_number(self.balance)
        else:
            _balances[x] = ERC20(_coin).balanceOf(_pool)


        _decimals: uint256 = convert(slice(_decimals_packed, x, 1), uint256)
        _precisions[x] = 10 ** (18 - _decimals)

        if _coin == self.pool_data[_pool].ul_coins[x]:
            _rates[x] = 10 ** 18
        else:
            _rate_method_id: bytes[4] = slice(self.pool_data[_pool].rate_method_id, 0, 4)
            _response: bytes[32] = raw_call(_coin, _rate_method_id, outsize=32)  # dev: bad response
            _rates[x] = convert(_response, uint256)

    return Calculator(self.pool_data[_pool].calculator).get_dx(
        _n_coins, _balances, _amp, _fee, _rates, _precisions, _is_underlying, i, j, _amount
    )


@public
def get_exchange_amounts(
    _pool: address,
    _from: address,
    _to: address,
    _amounts: uint256[CALC_INPUT_SIZE]
) -> uint256[CALC_INPUT_SIZE]:
    """
    @notice Get the current number of coins received in exchanges of varying amounts
    @param _pool Pool address
    @param _from Address of coin to be sent
    @param _to Address of coin to be received
    @param _amounts Array of quantities of `_from` to be sent
    @return Array of quantities of `_to` to be received
    """

    i: int128 = 0
    j: int128 = 0
    _is_underlying: bool = False
    i, j, _is_underlying = self._get_token_indices(_pool, _from, _to)

    _amp: uint256 = CurvePool(_pool).A()
    _fee: uint256 = CurvePool(_pool).fee()

    _decimals_packed: bytes32 = EMPTY_BYTES32
    if _is_underlying:
        _decimals_packed = self.pool_data[_pool].underlying_decimals
    else:
        _decimals_packed = self.pool_data[_pool].decimals

    _rates: uint256[MAX_COINS] = EMPTY_UINT256_ARRAY
    _balances: uint256[MAX_COINS] = EMPTY_UINT256_ARRAY
    _precisions: uint256[MAX_COINS] = EMPTY_UINT256_ARRAY
    _n_coins: int128 = 0
    _coin: address = ZERO_ADDRESS
    for x in range(MAX_COINS):
        _coin = self.pool_data[_pool].coins[x]

        if _coin == ZERO_ADDRESS:
            _n_coins = x
            break

        if _coin == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
            _balances[x] = as_unitless_number(self.balance)
        else:
            _balances[x] = ERC20(_coin).balanceOf(_pool)

        _decimals: uint256 = convert(slice(_decimals_packed, x, 1), uint256)
        _precisions[x] = 10 ** (18 - _decimals)

        if _coin == self.pool_data[_pool].ul_coins[x]:
            _rates[x] = 10 ** 18
        else:
            _rate_method_id: bytes[4] = slice(self.pool_data[_pool].rate_method_id, 0, 4)
            _response: bytes[32] = raw_call(_coin, _rate_method_id, outsize=32)  # dev: bad response
            _rates[x] = convert(_response, uint256)

    return Calculator(self.pool_data[_pool].calculator).get_dy(
        _n_coins, _balances, _amp, _fee, _rates, _precisions, _is_underlying, i, j, _amounts
    )


# Admin functions

@private
def _add_pool(
    _pool: address,
    _n_coins: int128,
    _lp_token: address,
    _calculator: address,
    _rate_method_id: bytes32,
    _coins: address[MAX_COINS],
    _ucoins: address[MAX_COINS],
    _decimals: bytes32,
    _udecimals: bytes32,
):
    # add pool to pool_list
    _length: uint256 = self.pool_count
    self.pool_list[_length] = _pool
    self.pool_count = _length + 1
    self.pool_data[_pool].location = _length
    self.pool_data[_pool].lp_token = _lp_token
    self.pool_data[_pool].calculator = _calculator
    self.pool_data[_pool].rate_method_id = _rate_method_id

    _decimals_packed: uint256 = 0
    _udecimals_packed: uint256 = 0

    for i in range(MAX_COINS):
        if i == _n_coins:
            break

        # add decimals
        _value: uint256 = convert(slice(_decimals, i, 1), uint256)
        if _value == 0:
            if _coins[i] == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
                _value = 18
            else:
                _value = ERC20(_coins[i]).decimals()
                assert _value < 256  # dev: decimal overflow

        _decimals_packed += shift(_value, (31-i) * 8)

        if _ucoins[i] != ZERO_ADDRESS:
            _value = convert(slice(_udecimals, i, 1), uint256)
            if _value == 0:
                if _ucoins[i] == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
                    _value = 18
                else:
                    _value = ERC20(_ucoins[i]).decimals()
                    assert _value < 256  # dev: decimal overflow

            _udecimals_packed += shift(_value, (31-i) * 8)

        # add pool to markets
        for x in range(i, i + MAX_COINS):
            if x == i:
                continue
            if x == _n_coins:
                break

            _first: uint256 = min(convert(_coins[i], uint256), convert(_coins[x], uint256))
            _second: uint256 = max(convert(_coins[i], uint256), convert(_coins[x], uint256))

            _pool_zero: uint256 = self.markets[_first][_second][0]
            if _pool_zero != 0:
                _length = _pool_zero % 65536
                self.markets[_first][_second][_length] = convert(_pool, uint256)
                self.markets[_first][_second][0] = _pool_zero + 1
            else:
                self.markets[_first][_second][0] = shift(convert(_pool, uint256), 16) + 1

            if _ucoins[i] == ZERO_ADDRESS:
                continue
            if _ucoins[x] == ZERO_ADDRESS:
                continue
            if _ucoins[i] == _coins[i] and _ucoins[x] == _coins[x]:
                continue

            _first = min(convert(_ucoins[i], uint256), convert(_ucoins[x], uint256))
            _second = max(convert(_ucoins[i], uint256), convert(_ucoins[x], uint256))

            _pool_zero = self.markets[_first][_second][0]

            if _pool_zero != 0:
                _length = _pool_zero % 65536
                self.markets[_first][_second][_length] = convert(_pool, uint256)
                self.markets[_first][_second][0] = _pool_zero + 1
            else:
                self.markets[_first][_second][0] = shift(convert(_pool, uint256), 16) + 1

    self.pool_data[_pool].decimals = convert(_decimals_packed, bytes32)
    self.pool_data[_pool].underlying_decimals = convert(_udecimals_packed, bytes32)
    log.PoolAdded(_pool, slice(_rate_method_id, 0, 4))


@public
def add_pool(
    _pool: address,
    _n_coins: int128,
    _lp_token: address,
    _calculator: address,
    _rate_method_id: bytes32,
    _decimals: bytes32,
    _underlying_decimals: bytes32,
):
    """
    @notice Add a pool to the registry
    @dev Only callable by admin
    @param _pool Pool address to add
    @param _n_coins Number of coins in the pool
    @param _lp_token Pool deposit token address
    @param _rate_method_id Encoded four-byte function signature to query
                           coin rates, right padded to bytes32
    @param _decimals Coin decimal values, tightly packed as uint8 and right
                     padded as bytes32
    @param _underlying_decimals Underlying coin decimal values, tightly packed
                                as uint8 and right padded as bytes32
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.pool_data[_pool].coins[0] == ZERO_ADDRESS  # dev: pool exists

    _coins: address[MAX_COINS] = EMPTY_ADDRESS_ARRAY
    _ucoins: address[MAX_COINS] = EMPTY_ADDRESS_ARRAY

    for i in range(MAX_COINS):
        if i == _n_coins:
            break

        # add coin
        _coins[i] = CurvePool(_pool).coins(i)
        if _coins[i] != 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
            ERC20(_coins[i]).approve(_pool, MAX_UINT256)
        self.pool_data[_pool].coins[i] = _coins[i]

        # add underlying coin
        _ucoins[i] = CurvePool(_pool).underlying_coins(i)
        if _ucoins[i] != _coins[i]:
            if _ucoins[i] != 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
                ERC20(_ucoins[i]).approve(_pool, MAX_UINT256)
        self.pool_data[_pool].ul_coins[i] = _ucoins[i]

    self._add_pool(
        _pool,
        _n_coins,
        _lp_token,
        _calculator,
        _rate_method_id,
        _coins,
        _ucoins,
        _decimals,
        _underlying_decimals
    )


@public
def add_pool_without_underlying(
    _pool: address,
    _n_coins: int128,
    _lp_token: address,
    _calculator: address,
    _rate_method_id: bytes32,
    _decimals: bytes32,
    _use_rates: bytes32,
):
    """
    @notice Add a pool to the registry
    @dev Only callable by admin
    @param _pool Pool address to add
    @param _n_coins Number of coins in the pool
    @param _lp_token Pool deposit token address
    @param _rate_method_id Encoded four-byte function signature to query
                           coin rates, right padded as bytes32
    @param _decimals Coin decimal values, tightly packed as uint8 and right
                     padded as bytes32
    @param _use_rates Boolean array indicating which coins use lending rates,
                      tightly packed and right padded as bytes32
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.pool_data[_pool].coins[0] == ZERO_ADDRESS  # dev: pool exists

    _coins: address[MAX_COINS] = EMPTY_ADDRESS_ARRAY
    _ucoins: address[MAX_COINS] = EMPTY_ADDRESS_ARRAY
    _use_rates_mem: bytes32 = _use_rates

    for i in range(MAX_COINS):
        if i == _n_coins:
            break

        # add coin
        _coins[i] = CurvePool(_pool).coins(i)
        if _coins[i] != 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
            ERC20(_coins[i]).approve(_pool, MAX_UINT256)
        self.pool_data[_pool].coins[i] = _coins[i]

        # add underlying coin
        if not convert(slice(_use_rates_mem, i, 1), bool):
            _ucoins[i] = _coins[i]
            self.pool_data[_pool].ul_coins[i] = _ucoins[i]

    self._add_pool(
        _pool,
        _n_coins,
        _lp_token,
        _calculator,
        _rate_method_id,
        _coins,
        _ucoins,
        _decimals,
        EMPTY_BYTES32
    )


@public
def remove_pool(_pool: address):
    """
    @notice Remove a pool to the registry
    @dev Only callable by admin
    @param _pool Pool address to remove
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.pool_data[_pool].coins[0] != ZERO_ADDRESS  # dev: pool does not exist

    # remove _pool from pool_list
    _location: uint256 = self.pool_data[_pool].location
    _length: uint256 = self.pool_count - 1

    if _location < _length:
        # replace _pool with final value in pool_list
        _addr: address = self.pool_list[_length]
        self.pool_list[_location] = _addr
        self.pool_data[_addr].location = _location

    # delete final pool_list value
    self.pool_list[_length] = ZERO_ADDRESS
    self.pool_count = _length

    _coins: address[MAX_COINS] = EMPTY_ADDRESS_ARRAY
    _ucoins: address[MAX_COINS] = EMPTY_ADDRESS_ARRAY

    for i in range(MAX_COINS):
        _coins[i] = self.pool_data[_pool].coins[i]
        if _coins[i] == ZERO_ADDRESS:
            break

        # delete coin address from pool_data
        self.pool_data[_pool].coins[i] = ZERO_ADDRESS

        # delete underlying_coin from pool_data
        _ucoins[i] = self.pool_data[_pool].ul_coins[i]
        self.pool_data[_pool].ul_coins[i] = ZERO_ADDRESS

    for i in range(MAX_COINS):
        if _coins[i] == ZERO_ADDRESS:
            break

        # remove pool from markets
        for x in range(i, i + MAX_COINS):
            if x == i:
                continue
            if _coins[x] == ZERO_ADDRESS:
                break

            _first: uint256 = min(convert(_coins[i], uint256), convert(_coins[x], uint256))
            _second: uint256 = max(convert(_coins[i], uint256), convert(_coins[x], uint256))

            _pool_zero: uint256 = self.markets[_first][_second][0]
            _length = _pool_zero % 65536 - 1
            if _length == 0:
                self.markets[_first][_second][0] = 0
            elif shift(_pool_zero, -16) == convert(_pool, uint256):
                self.markets[_first][_second][0] = shift(self.markets[_first][_second][_length], 16) + _length
                self.markets[_first][_second][_length] = 0
            else:
                self.markets[_first][_second][0] = _pool_zero - 1
                for n in range(1, 65536):
                    if n == convert(_length, int128):
                        break
                    if self.markets[_first][_second][n] == convert(_pool, uint256):
                        self.markets[_first][_second][n] = self.markets[_first][_second][_length]
                self.markets[_first][_second][_length] = 0

            if _ucoins[i] == _coins[i] and _ucoins[x] == _coins[x]:
                continue

            _first = min(convert(_ucoins[i], uint256), convert(_ucoins[x], uint256))
            _second = max(convert(_ucoins[i], uint256), convert(_ucoins[x], uint256))
            _pool_zero = self.markets[_first][_second][0]
            _length = _pool_zero % 65536 - 1
            if _length == 0:
                self.markets[_first][_second][0] = 0
            elif shift(_pool_zero, -16) == convert(_pool, uint256):
                self.markets[_first][_second][0] = shift(self.markets[_first][_second][_length], 16) + _length
                self.markets[_first][_second][_length] = 0
            else:
                self.markets[_first][_second][0] = _pool_zero - 1
                for n in range(1, 65536):
                    if n == convert(_length, int128):
                        break
                    if self.markets[_first][_second][n] == convert(_pool, uint256):
                        self.markets[_first][_second][n] = self.markets[_first][_second][_length]
                self.markets[_first][_second][_length] = 0

    log.PoolRemoved(_pool)


@public
def set_returns_none(_addr: address, _is_returns_none: bool):
    """
    @notice Set `returns_none` value for a coin
    @param _addr Coin address
    @param _is_returns_none if True, coin returns None on a successful transfer
    """
    assert msg.sender == self.admin  # dev: admin-only function

    self.returns_none[_addr] = _is_returns_none


@public
def set_pool_gas_estimates(_addr: address[5], _amount: uint256[2][5]):
    """
    @notice Set gas estimate amounts
    @param _addr Array of pool addresses
    @param _amount Array of gas estimate amounts as `[(wrapped, underlying), ..]`
    """
    assert msg.sender == self.admin  # dev: admin-only function

    for i in range(5):
        if _addr[i] == ZERO_ADDRESS:
            break
        self.gas_estimate_values[_addr[i]] = _amount[i]


@public
def set_coin_gas_estimates(_addr: address[10], _amount: uint256[10]):
    """
    @notice Set gas estimate amounts
    @param _addr Array of coin addresses
    @param _amount Array of gas estimate amounts
    """
    assert msg.sender == self.admin  # dev: admin-only function

    for i in range(10):
        if _addr[i] == ZERO_ADDRESS:
            break
        self.gas_estimate_values[_addr[i]][0] = _amount[i]


@public
def set_gas_estimate_contract(_pool: address, _estimator: address):
    """
    @notice Set gas estimate contract
    @param _pool Pool address
    @param _estimator GasEstimator address
    """
    assert msg.sender == self.admin  # dev: admin-only function

    self.gas_estimate_contracts[_pool] = _estimator


@public
def set_calculator(_pool: address, _calculator: address):
    """
    @notice Set calculator contract
    @dev Used to calculate `get_dy` for a pool
    @param _pool Pool address
    @param _calculator `CurveCalc` address
    """
    assert msg.sender == self.admin  # dev: admin-only function

    self.pool_data[_pool].calculator = _calculator


@public
@constant
def get_calculator(_pool: address) -> address:
    return self.pool_data[_pool].calculator


@public
def commit_transfer_ownership(_new_admin: address):
    """
    @notice Initiate a transfer of contract ownership
    @dev Once initiated, the actual transfer may be performed three days later
    @param _new_admin Address of the new owner account
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.transfer_ownership_deadline == 0  # dev: transfer already active

    _deadline: uint256 = as_unitless_number(block.timestamp) + 3*86400
    self.transfer_ownership_deadline = _deadline
    self.future_admin = _new_admin

    log.CommitNewAdmin(_deadline, _new_admin)


@public
def apply_transfer_ownership():
    """
    @notice Finalize a transfer of contract ownership
    @dev May only be called by the current owner, three days after a
         call to `commit_transfer_ownership`
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.transfer_ownership_deadline != 0  # dev: transfer not active
    assert block.timestamp >= self.transfer_ownership_deadline  # dev: now < deadline

    _new_admin: address = self.future_admin
    self.admin = _new_admin
    self.transfer_ownership_deadline = 0

    log.NewAdmin(_new_admin)


@public
def revert_transfer_ownership():
    """
    @notice Revert a transfer of contract ownership
    @dev May only be called by the current owner
    """
    assert msg.sender == self.admin  # dev: admin-only function

    self.transfer_ownership_deadline = 0


@public
def claim_token_balance(_token: address):
    """
    @notice Transfer any ERC20 balance held by this contract
    @dev The entire balance is transferred to `self.admin`
    @param _token Token address
    """
    assert msg.sender == self.admin  # dev: admin-only function

    _balance: uint256 = ERC20(_token).balanceOf(self)
    ERC20(_token).transfer(msg.sender, _balance)


@public
def claim_eth_balance():
    """
    @notice Transfer ether balance held by this contract
    @dev The entire balance is transferred to `self.admin`
    """
    assert msg.sender == self.admin  # dev: admin-only function

    send(msg.sender, self.balance)
