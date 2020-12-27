# @version 0.2.8
"""
@title CRV Zap Locker
@author Curve Finance
@license MIT
@notice Mint/claim CRV and lock it in the `VotingEscrow` in a single action
"""


from vyper.interfaces import ERC20

interface VotingEscrow:
    def deposit_for(_addr: address, _value: uint256): nonpayable

interface VestingEscrow:
    def claim(addr: address): nonpayable

interface Minter:
    def mint_for(gauge_addr: address, _for: address): nonpayable


CRV: constant(address) = 0xD533a949740bb3306d119CC777fa900bA034cd52
MINTER: constant(address) = 0xd061D61a4d941c39E5453435B6345Dc261C2fcE0
VESTING_ESCROW: constant(address) = 0x575CCD8e2D300e2377B43478339E364000318E2c
VOTING_ESCROW: constant(address) = 0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2


@external
def mint_and_lock(_gauges: address[20]) -> bool:
    """
    @notice Mint and lock CRV
    @param _gauges List of LiquidityGauge contracts to mint from
    @return bool success
    """
    initial_amount: uint256 = ERC20(CRV).balanceOf(msg.sender)

    for gauge in _gauges:
        if gauge == ZERO_ADDRESS:
            break
        Minter(MINTER).mint_for(gauge, msg.sender)

    lock_amount: uint256 = ERC20(CRV).balanceOf(msg.sender) - initial_amount
    VotingEscrow(VOTING_ESCROW).deposit_for(msg.sender, lock_amount)

    return True


@external
def claim_vested_and_lock() -> bool:
    """
    @notice Claim and lock vested CRV
    @return bool success
    """
    initial_amount: uint256 = ERC20(CRV).balanceOf(msg.sender)

    VestingEscrow(VESTING_ESCROW).claim(msg.sender)

    lock_amount: uint256 = ERC20(CRV).balanceOf(msg.sender) - initial_amount
    VotingEscrow(VOTING_ESCROW).deposit_for(msg.sender, lock_amount)

    return True


@external
def mint_claim_and_lock(_gauges: address[20]) -> bool:
    """
    @notice Mint, claim and lock CRV
    @param _gauges List of LiquidityGauge contracts to mint from
    @return bool success
    """
    initial_amount: uint256 = ERC20(CRV).balanceOf(msg.sender)

    VestingEscrow(VESTING_ESCROW).claim(msg.sender)
    for gauge in _gauges:
        if gauge == ZERO_ADDRESS:
            break
        Minter(MINTER).mint_for(gauge, msg.sender)

    lock_amount: uint256 = ERC20(CRV).balanceOf(msg.sender) - initial_amount
    VotingEscrow(VOTING_ESCROW).deposit_for(msg.sender, lock_amount)

    return True
