# @version 0.3.3
"""
@title EURT Burner
@notice Deposits EURT into EURT/am3CRV Crypto Pool and returns LP token
"""
from vyper.interfaces import ERC20


interface ECrypto:
    def add_liquidity(_amounts: uint256[2], _min_dy: uint256) -> uint256: nonpayable


EURT: constant(address) = 0x7BDF330f423Ea880FF95fC41A280fD5eCFD3D09f  # EURT
POOL: constant(address) = 0xB446BF7b8D6D4276d0c75eC0e3ee8dD7Fe15783A  # EURT/am3CRV
LP_TOKEN: constant(address) = 0x600743B1d8A96438bD46836fD34977a00293f6Aa  # crvEURTUSD


receiver: public(address)

owner: public(address)
future_owner: public(address)


@external
def __init__(receiver: address):
    ERC20(EURT).approve(POOL, MAX_UINT256)

    self.receiver = receiver
    self.owner = msg.sender


@external
def burn(_coin: address) -> bool:
    amount: uint256 = ERC20(_coin).balanceOf(msg.sender)
    ERC20(_coin).transferFrom(msg.sender, self, amount)

    amount = ECrypto(POOL).add_liquidity([amount, 0], 0)
    ERC20(LP_TOKEN).transfer(self.receiver, amount)

    return True


@external
def recover_balance(_coin: address) -> bool:
    """
    @notice Recover ERC20 tokens from this contract
    @dev Tokens are sent to the recovery address
    @param _coin Token address
    @return bool success
    """
    assert msg.sender == self.owner

    amount: uint256 = ERC20(_coin).balanceOf(self)
    response: Bytes[32] = raw_call(
        _coin,
        concat(
            method_id("transfer(address,uint256)"),
            convert(msg.sender, bytes32),
            convert(amount, bytes32),
        ),
        max_outsize=32,
    )
    if len(response) != 0:
        assert convert(response, bool)

    return True


@external
def set_receiver(_receiver: address) -> bool:
    """
    @notice Set the token receiver address
    @return bool success
    """
    assert msg.sender == self.owner  # dev: only owner
    self.receiver = _receiver

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
