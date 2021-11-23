# @version 0.3.0
"""
@title cToken Burner
@notice Converts cToken lending coins to USDT
"""

from vyper.interfaces import ERC20


interface LendingPool:
    def withdraw(_underlying_asset: address, _amount: uint256, _receiver: address): nonpayable

interface cERC20:
    def redeem(redeemTokens: uint256) -> uint256: nonpayable
    def underlying() -> address: view

interface RegistrySwap:
    def exchange_with_best_rate(
        _from: address,
        _to: address,
        _amount: uint256,
        _expected: uint256,
        _receiver: address,
    ) -> uint256: payable

interface AddressProvider:
    def get_address(_id: uint256) -> address: view


receiver: public(address)
is_killed: public(bool)

owner: public(address)
future_owner: public(address)

is_approved: HashMap[address, HashMap[address, bool]]

ADDRESS_PROVIDER: constant(address) = 0x0000000022D53366457F9d5E68Ec105046FC4383
USDT: constant(address) = 0x049d68029688eAbF473097a2fC38ef61633A3C7A


@external
def __init__(_receiver: address, _owner: address):
    """
    @notice Contract constructor
    @param _receiver Address that converted tokens are transferred to.
                     Should be set to the `ChildBurner` deployment.
    @param _owner Owner address. Can kill the contract and recover tokens.
    """
    self.receiver = _receiver
    self.owner = _owner


@external
def burn(_coin: address) -> bool:
    """
    @notice Unwrap `_coin` and transfer to the underlying burner
    @param _coin Address of the coin being unwrapped
    @return bool success
    """
    assert not self.is_killed  # dev: is killed

    # transfer coins from caller
    amount: uint256 = ERC20(_coin).balanceOf(msg.sender)
    if amount != 0:
        ERC20(_coin).transferFrom(msg.sender, self, amount)

    # get actual balance in case of transfer fee or pre-existing balance
    amount = ERC20(_coin).balanceOf(self)


    # unwrap cTokens for underlying asset
    assert cERC20(_coin).redeem(amount) == 0
    underlying: address = cERC20(_coin).underlying()
    amount = ERC20(underlying).balanceOf(self)

    if underlying == USDT:
        response: Bytes[32] = raw_call(
            underlying,
            _abi_encode(self.receiver, amount, method_id=method_id("transfer(address,uint256)")),
            max_outsize=32,
        )
        if len(response) != 0:
            assert convert(response, bool)
    else:
        registry_swap: address = AddressProvider(ADDRESS_PROVIDER).get_address(2)
        if not self.is_approved[registry_swap][underlying]:
            response: Bytes[32] = raw_call(
                underlying,
                _abi_encode(registry_swap, MAX_UINT256, method_id=method_id("approve(address,uint256)")),
                max_outsize=32,
            )
            if len(response) != 0:
                assert convert(response, bool)
            self.is_approved[registry_swap][underlying] = True

        RegistrySwap(registry_swap).exchange_with_best_rate(underlying, USDT, amount, 0, self.receiver)

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
