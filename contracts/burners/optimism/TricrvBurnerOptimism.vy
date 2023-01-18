# @version 0.3.7
"""
@title Stable Burner
@notice Deposits coins into 3pool
"""

from vyper.interfaces import ERC20

interface StableSwap:
    def add_liquidity(_amounts: uint256[N_COINS], _min_mint_amount: uint256, _receiver: address): nonpayable
    def coins(_i: uint256) -> address: view


receiver: address
is_killed: public(bool)

owner: public(address)
future_owner: public(address)

N_COINS: constant(uint256) = 3
POOL: immutable(address)
COINS: immutable(address[N_COINS])


@external
def __init__(_pool: address, _receiver: address, _owner: address):
    """
    @notice Contract constructor
    @param _pool Address of the pool to deposit into
    @param _receiver Address that converted tokens are transferred to.
                     Should be set to the `ChildBurner` deployment.
    @param _owner Owner address. Can kill the contract and recover tokens.
    """
    self.receiver = _receiver
    self.owner = _owner

    POOL = _pool

    coins: address[N_COINS] = empty(address[N_COINS])
    for i in range(N_COINS):
        coins[i] = StableSwap(_pool).coins(i)
    COINS = coins

    for coin in coins:
        ERC20(coin).approve(_pool, max_value(uint256))


@external
def burn(_coin: address) -> bool:
    """
    @notice Convert `_coin` by depositing it in the pool
    @param _coin Address of the coin being converted
    @return bool success
    """
    assert not self.is_killed  # dev: is killed
    assert _coin in COINS

    # transfer coins from caller
    amount: uint256 = ERC20(_coin).balanceOf(msg.sender)
    if amount != 0:
        ERC20(_coin).transferFrom(msg.sender, self, amount)

    # deposit only once
    if _coin != COINS[N_COINS - 1]:
        return True

    amounts: uint256[N_COINS] = empty(uint256[N_COINS])
    for i in range(N_COINS):
        amounts[i] = ERC20(COINS[i]).balanceOf(self)
    StableSwap(POOL).add_liquidity(amounts, 0, self.receiver)

    return True


@external
def recover_balance(_coin: address) -> bool:
    """
    @notice Recover ERC20 tokens from this contract
    @param _coin Token address
    @return bool success
    """
    assert msg.sender == self.owner  # dev: only owner

    amount: uint256 = ERC20(_coin).balanceOf(self)
    response: Bytes[32] = raw_call(
        _coin,
        _abi_encode(msg.sender, amount, method_id=method_id("transfer(address,uint256)")),
        max_outsize=32,
    )
    if len(response) != 0:
        assert convert(response, bool)

    return True


@external
def set_receiver(_receiver: address):
    assert msg.sender == self.owner
    self.receiver = _receiver


@external
def set_killed(_is_killed: bool) -> bool:
    """
    @notice Set killed status for this contract
    @dev When killed, the `burn` function cannot be called
    @param _is_killed Killed status
    @return bool success
    """
    assert msg.sender == self.owner  # dev: only owner
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
