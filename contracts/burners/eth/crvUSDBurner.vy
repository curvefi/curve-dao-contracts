# @version 0.3.7
"""
@title crvUSD Burner
@notice Withdraws LP tokens from crvUSD pools and exchanges crvUSD
"""


interface ERC20:
    def approve(_to: address, _value: uint256): nonpayable
    def transferFrom(_from: address, _to: address, _value: uint256) -> bool: nonpayable
    def balanceOf(_owner: address) -> uint256: view
    def decimals() -> uint256: view


interface StableSwap:
    def coins(_i: uint256) -> address: view
    def price_oracle() -> uint256: view
    def get_virtual_price() -> uint256: view
    def get_dy(i: int128, j: int128, dx: uint256) -> uint256: view
    def remove_liquidity_one_coin(token_amount: uint256, i: int128, min_amount: uint256,
                                  receiver: address = msg.sender) -> uint256: nonpayable
    def exchange(i: int128, j: int128, _dx: uint256, _min_dy: uint256, _receiver: address = msg.sender) -> uint256: nonpayable


interface PoolProxy:
    def burners(_coin: address) -> address: view


struct RemoveIn:
    adjustment: uint64
    i: uint8  # crvUSD index
    not_crvUSD: bool  # Remove crvUSD if not prioritized pool(from self.pools)


N_COINS: constant(uint8) = 2
MAX_NUM: constant(uint256) = 8  # max number of coins more prioritized than crvUSD
BPS: constant(uint256) = 10000  # precision
SLIPPAGE: constant(uint256) = 2 * 100  # in BPS, 2%
crvUSD: immutable(address)

pools: public(DynArray[address, MAX_NUM])
remove_in: public(HashMap[address, RemoveIn])

slippage_of: public(HashMap[address, uint256])

pool_proxy: public(address)
recovery: public(address)
is_killed: public(bool)

owner: public(address)
emergency_owner: public(address)
manager: public(address)
future_owner: public(address)
future_emergency_owner: public(address)
future_manager: public(address)


@external
def __init__(_crvUSD: address, _pool_proxy: address, _owner: address, _emergency_owner: address):
    """
    @notice Contract constructor
    @dev Unlike other burners, this contract may transfer tokens to
         multiple addresses after the swap. Receiver addresses are
         set by calling `set_swap_data` instead of setting it
         within the constructor.
    @param _crvUSD Address of crvUSD
    @param _pool_proxy Address of pool owner proxy
    @param _owner Owner address. Can kill the contract, recover tokens
                  and modify the recovery address.
    @param _emergency_owner Emergency owner address. Can kill the contract
                            and recover tokens.
    """
    crvUSD = _crvUSD
    self.pool_proxy = _pool_proxy
    self.recovery = _pool_proxy
    self.owner = _owner
    self.emergency_owner = _emergency_owner
    self.manager = msg.sender


@internal
def _burn(_coin: address, _amount: uint256) -> bool:
    if _coin != crvUSD:
        # LP token of crvUSD pool
        info: RemoveIn = self.remove_in[_coin]
        if info.adjustment == 0:
            # New coin, remove in crvUSD
            if StableSwap(_coin).coins(1) == crvUSD:
                info.i = 1
            info.adjustment = 1  # crvUSD is 18 decimals
            self.remove_in[_coin] = info

        i: int128 = convert(info.i, int128)
        receiver: address = self
        if info.not_crvUSD:
            i = 1 - i
            receiver = self.pool_proxy

        price: uint256 = StableSwap(_coin).price_oracle()
        min_amount: uint256 = _amount * StableSwap(_coin).get_virtual_price() / 10 ** 18
        if info.i == 0:
            min_amount = min_amount * 10 ** 18 / price
        else:
            min_amount = min_amount * price / 10 ** 18

        # Decimals difference
        min_amount /= convert(info.adjustment, uint256)

        # Account slippage
        slippage: uint256 = self.slippage_of[_coin]
        if slippage == 0:
            slippage = SLIPPAGE
        min_amount -= min_amount * slippage / BPS

        StableSwap(_coin).remove_liquidity_one_coin(_amount, i, min_amount, receiver)
    else:
        # Find the best available pool by dy
        best_dy: uint256 = 0
        best_pool: address = empty(address)
        i: int128 = 0
        for pool in self.pools:
            info: RemoveIn = self.remove_in[pool]
            dy: uint256 = StableSwap(pool).get_dy(
                convert(info.i, int128), 1 - convert(info.i, int128), _amount
            ) * convert(info.adjustment, uint256)

            if dy > best_dy:
                best_dy = dy
                best_pool = pool
                i = convert(info.i, int128)

        StableSwap(best_pool).exchange(i, 1 - i, _amount, 0, self.pool_proxy)  # best_dy is already counted

    return True


@payable
@external
def burn(_coin: ERC20) -> bool:
    """
    @notice Swap `_coin` for 3CRV and transfer to the fee distributor
    @param _coin Address of the coin being swapped
    @return bool success
    """
    assert not self.is_killed  # dev: is killed

    # transfer coins from caller
    amount: uint256 = _coin.balanceOf(msg.sender)
    if amount != 0:
        _coin.transferFrom(msg.sender, self, amount)

    # get actual balance in case of transfer fee or pre-existing balance
    amount = _coin.balanceOf(self)

    return self._burn(_coin.address, amount)


@external
def burn_amount(_coin: ERC20, _amount_to_burn: uint256):
    """
    @notice Burn a specific quantity of `_coin`
    @dev Useful when the total amount to burn is so large that it fails from slippage
    @param _coin Address of the coin being converted
    @param _amount_to_burn Amount of the coin to burn
    """
    assert not self.is_killed  # dev: is killed

    pool_proxy: address = self.pool_proxy
    amount: uint256 = _coin.balanceOf(pool_proxy)
    if PoolProxy(pool_proxy).burners(_coin.address) == self and amount != 0:
        _coin.transferFrom(pool_proxy, self, amount)

    amount = _coin.balanceOf(self)
    assert amount >= _amount_to_burn, "Insufficient balance"

    self._burn(_coin.address, _amount_to_burn)


@external
def set_pools(_pools: DynArray[address, MAX_NUM]):
    """
    @notice Set new prioritized pools
    @param _pools Addresses of prioritized pools
    """
    assert msg.sender in [self.owner, self.manager]
    assert len(_pools) > 0

    for pool in self.pools:
        self.remove_in[pool] = empty(RemoveIn)
        ERC20(crvUSD).approve(pool, 0)

    self.pools = _pools

    for pool in _pools:
        info: RemoveIn = empty(RemoveIn)
        info.i = N_COINS
        for i in range(N_COINS):
            coin: address = StableSwap(pool).coins(convert(i, uint256))
            if coin == crvUSD:
                info.i = i
            else:
                info.adjustment = convert(10 ** (18 - ERC20(coin).decimals()), uint64)
        assert info.i < N_COINS  # dev: pool does not contain crvUSD
        info.not_crvUSD = True

        self.remove_in[pool] = info
        ERC20(crvUSD).approve(pool, max_value(uint256))


@external
def recover_balance(_coin: address) -> bool:
    """
    @notice Recover ERC20 tokens from this contract
    @dev Tokens are sent to the recovery address
    @param _coin Token address
    @return bool success
    """
    assert msg.sender in [self.owner, self.emergency_owner]  # dev: only owner

    amount: uint256 = ERC20(_coin).balanceOf(self)
    response: Bytes[32] = raw_call(
        _coin,
        _abi_encode(self.recovery, amount, method_id=method_id("transfer(address,uint256)")),
        max_outsize=32,
    )
    if len(response) != 0:
        assert convert(response, bool)

    return True


@external
def set_recovery(_recovery: address) -> bool:
    """
    @notice Set the token recovery address
    @param _recovery Token recovery address
    @return bool success
    """
    assert msg.sender == self.owner  # dev: only owner
    self.recovery = _recovery

    return True


@external
def set_killed(_is_killed: bool) -> bool:
    """
    @notice Set killed status for this contract
    @dev When killed, the `burn` function cannot be called
    @param _is_killed Killed status
    @return bool success
    """
    assert msg.sender in [self.owner, self.emergency_owner]  # dev: only owner
    self.is_killed = _is_killed

    return True



@external
def commit_transfer_ownership(_future_owner: address) -> bool:
    """
    @notice Commit a transfer of ownership
    @dev Must be accepted by the new owner via `accept_transfer_ownership`
    @param _future_owner New owner address
    @return bool success
    """
    assert msg.sender == self.owner  # dev: only owner
    self.future_owner = _future_owner

    return True


@external
def accept_transfer_ownership() -> bool:
    """
    @notice Accept a transfer of ownership
    @return bool success
    """
    assert msg.sender == self.future_owner  # dev: only owner
    self.owner = msg.sender

    return True


@external
def commit_transfer_emergency_ownership(_future_owner: address) -> bool:
    """
    @notice Commit a transfer of ownership
    @dev Must be accepted by the new owner via `accept_transfer_ownership`
    @param _future_owner New owner address
    @return bool success
    """
    assert msg.sender == self.emergency_owner  # dev: only owner
    self.future_emergency_owner = _future_owner

    return True


@external
def accept_transfer_emergency_ownership() -> bool:
    """
    @notice Accept a transfer of ownership
    @return bool success
    """
    assert msg.sender == self.future_emergency_owner  # dev: only owner
    self.emergency_owner = msg.sender

    return True


@external
def commit_new_manager(_future_manager: address) -> bool:
    """
    @notice Commit a transfer of manager's role
    @dev Must be accepted by the new manager via `accept_new_manager`
    @param _future_manager New manager address
    @return bool success
    """
    assert msg.sender in [self.owner, self.emergency_owner, self.manager]  # dev: only owner
    self.future_manager = _future_manager

    return True


@external
def accept_new_manager() -> bool:
    """
    @notice Accept a transfer of manager's role
    @return bool success
    """
    assert msg.sender == self.future_manager  # dev: only owner
    self.manager = msg.sender

    return True
