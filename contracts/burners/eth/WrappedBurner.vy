# @version 0.3.3
"""
@title Wrapped ETH Burner
@notice Withdraws ETH from Wrapped ETH
"""


interface wETH:
    def balanceOf(_owner: address) -> uint256: view
    def transferFrom(_sender: address, _receiver: address, _amount: uint256): nonpayable
    def withdraw(_amount: uint256): nonpayable


WETH: immutable(wETH)
RECEIVER: immutable(address)


@external
def __init__(_weth: address, _receiver: address):
    """
    @notice Contract constructor
    @param _weth Address of wrapped ETh
    @param _receiver Address of receiver of ETH
    """
    WETH = wETH(_weth)
    RECEIVER = _receiver


@payable
@external
def __default__():
    pass


@external
def receiver() -> address:
    return RECEIVER


@external
def burn(_coin: address) -> bool:
    """
    @notice Unwrap ETH
    @param _coin Remained for compatability
    @return bool success
    """
    amount: uint256 = WETH.balanceOf(msg.sender)
    WETH.transferFrom(msg.sender, self, amount)
    amount = WETH.balanceOf(self)

    WETH.withdraw(amount)
    raw_call(RECEIVER, b"", value=amount)
    return True
