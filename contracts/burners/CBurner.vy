# @version 0.2.7
"""
@title cToken Burner
@notice Converts cTokens lending coins to USDC and transfers to `UnderlyingBurner`
"""

from vyper.interfaces import ERC20


interface cERC20:
    def redeem(redeemTokens: uint256) -> uint256: nonpayable
    def underlying() -> address: view


receiver: public(address)
owner: public(address)
future_owner: public(address)
is_killed: public(bool)


@external
def __init__(_receiver: address, _owner: address):
    """
    @notice Contract constructor
    @param _receiver Address that converted tokens are transferred to.
                     Should be set to an `UnderlyingBurner` deployment.
    @param _owner Owner address
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
    assert not self.is_killed

    # transfer coins from caller
    amount: uint256 = ERC20(_coin).balanceOf(msg.sender)
    ERC20(_coin).transferFrom(msg.sender, self, amount)

    # get actual balance in case of transfer fee or pre-existing balance
    amount = ERC20(_coin).balanceOf(self)

    # unwrap cTokens for underlying asset
    assert cERC20(_coin).redeem(amount) == 0
    underlying: address = cERC20(_coin).underlying()
    amount = ERC20(underlying).balanceOf(self)

    # transfer underlying to underlying burner
    response: Bytes[32] = raw_call(
        underlying,
        concat(
            method_id("transfer(address,uint256)"),
            convert(self.receiver, bytes32),
            convert(amount, bytes32),
        ),
        max_outsize=32,
    )
    if len(response) != 0:
        assert convert(response, bool)

    return True


@external
def commit_transfer_ownership(_future_owner: address) -> bool:
    """
    @notice Commit a transfer of ownership
    @dev Must be accepted by the new owner via `accept_transfer_ownership`
    @param _future_owner New owner address
    @return bool success
    """
    assert msg.sender == self.owner
    self.future_owner = _future_owner

    return True


@external
def accept_transfer_ownership() -> bool:
    """
    @notice Accept a transfer of ownership
    @return bool success
    """
    assert msg.sender == self.future_owner
    self.owner = msg.sender

    return True


@external
def recover_balance(_coin: address, _receiver: address) -> bool:
    """
    @notice Recover ERC20 tokens from this contract
    @dev Only callable by the owner
    @param _coin Token address
    @param _receiver Address to transfer tokens to
    @return bool success
    """
    assert msg.sender == self.owner

    amount: uint256 = ERC20(_coin).balanceOf(self)
    response: Bytes[32] = raw_call(
        _coin,
        concat(
            method_id("transfer(address,uint256)"),
            convert(_receiver, bytes32),
            convert(amount, bytes32),
        ),
        max_outsize=32,
    )
    if len(response) != 0:
        assert convert(response, bool)

    return True


@external
def set_killed(_is_killed: bool) -> bool:
    """
    @notice Set killed status for this contract
    @dev When killed, the `burn` function cannot be called
    @param _is_killed Killed status
    @return bool success
    """
    assert msg.sender == self.owner
    self.is_killed = _is_killed

    return True
