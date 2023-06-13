# @version 0.3.7
"""
@title Wrapped stETH Burner
@notice Withdraws stETH from Wrapped stETH
"""

from vyper.interfaces import ERC20


interface wstETH:
    def balanceOf(_owner: address) -> uint256: view
    def transferFrom(_sender: address, _receiver: address, _amount: uint256): nonpayable
    def unwrap(_wstETHAmount: uint256): nonpayable
    def stETH() -> address: view


WSTETH: immutable(wstETH)
STETH: immutable(ERC20)
RECEIVER: immutable(address)


@external
def __init__(_wsteth: wstETH, _receiver: address):
    """
    @notice Contract constructor
    @param _wsteth Address of wrapped stETH
    @param _receiver Address of receiver of stETH
    """
    WSTETH = _wsteth
    STETH = ERC20(_wsteth.stETH())
    RECEIVER = _receiver


@payable
@external
def __default__():
    pass


@view
@external
def receiver() -> address:
    return RECEIVER


@external
def burn(_coin: address) -> bool:
    """
    @notice Unwrap stETH
    @param _coin Remained for compatability
    @return bool success
    """
    amount: uint256 = WSTETH.balanceOf(msg.sender)
    WSTETH.transferFrom(msg.sender, self, amount)
    amount = WSTETH.balanceOf(self)
    WSTETH.unwrap(amount)

    amount = STETH.balanceOf(self)
    STETH.transfer(RECEIVER, amount)
    return True
