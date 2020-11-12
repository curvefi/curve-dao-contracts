# @version 0.2.7
"""
@title Tokenized Liquidity Gauge Wrapper
@author Curve Finance
@license MIT
@notice Allows tokenized deposits and claiming from `LiquidityGauge`
"""

from vyper.interfaces import ERC20

implements: ERC20

interface LiquidityGauge:
    def lp_token() -> address: view
    def minter() -> address: view
    def crv_token() -> address: view
    def deposit(_value: uint256): nonpayable
    def withdraw(_value: uint256): nonpayable
    def claimable_tokens(addr: address) -> uint256: nonpayable

interface Minter:
    def mint(gauge_addr: address): nonpayable


event Deposit:
    provider: indexed(address)
    value: uint256

event Withdraw:
    provider: indexed(address)
    value: uint256

event CommitOwnership:
    admin: address

event ApplyOwnership:
    admin: address

event Transfer:
    _from: indexed(address)
    _to: indexed(address)
    _value: uint256

event Approval:
    _owner: indexed(address)
    _spender: indexed(address)
    _value: uint256


minter: public(address)
crv_token: public(address)
lp_token: public(address)
gauge: public(address)

balanceOf: public(HashMap[address, uint256])
totalSupply: public(uint256)
allowances: HashMap[address, HashMap[address, uint256]]

name: public(String[64])
symbol: public(String[32])
decimals: public(uint256)

# caller -> recipient -> can deposit?
approved_to_deposit: public(HashMap[address, HashMap[address, bool]])

crv_integral: uint256
crv_integral_for: HashMap[address, uint256]
claimable_crv: public(HashMap[address, uint256])

admin: public(address)
future_admin: public(address)
is_killed: public(bool)


@external
def __init__(
    _name: String[64],
    _symbol: String[32],
    _gauge: address,
    _admin: address
):
    """
    @notice Contract constructor
    @param _name Token full name
    @param _symbol Token symbol
    @param _gauge Liquidity gauge contract address
    @param _admin Admin who can kill the gauge
    """

    self.name = _name
    self.symbol = _symbol
    self.decimals = 18

    lp_token: address = LiquidityGauge(_gauge).lp_token()
    ERC20(lp_token).approve(_gauge, MAX_UINT256)

    self.minter = LiquidityGauge(_gauge).minter()
    self.crv_token = LiquidityGauge(_gauge).crv_token()
    self.lp_token = lp_token
    self.gauge = _gauge
    self.admin = _admin


@internal
def _checkpoint(addr: address):
    crv_token: address = self.crv_token

    d_reward: uint256 = ERC20(crv_token).balanceOf(self)
    Minter(self.minter).mint(self.gauge)
    d_reward = ERC20(crv_token).balanceOf(self) - d_reward

    total_balance: uint256 = self.totalSupply
    dI: uint256 = 0
    if total_balance > 0:
        dI = 10 ** 18 * d_reward / total_balance
    I: uint256 = self.crv_integral + dI
    self.crv_integral = I
    self.claimable_crv[addr] += self.balanceOf[addr] * (I - self.crv_integral_for[addr]) / 10 ** 18
    self.crv_integral_for[addr] = I


@external
def user_checkpoint(addr: address) -> bool:
    """
    @notice Record a checkpoint for `addr`
    @param addr User address
    @return bool success
    """
    assert msg.sender == addr or msg.sender == self.minter  # dev: unauthorized
    self._checkpoint(addr)
    return True


@external
def claimable_tokens(addr: address) -> uint256:
    """
    @notice Get the number of claimable tokens per user
    @dev This function should be manually changed to "view" in the ABI
    @return uint256 number of claimable tokens per user
    """
    d_reward: uint256 = LiquidityGauge(self.gauge).claimable_tokens(self)

    total_balance: uint256 = self.totalSupply
    dI: uint256 = 0
    if total_balance > 0:
        dI = 10 ** 18 * d_reward / total_balance
    I: uint256 = self.crv_integral + dI

    return self.claimable_crv[addr] + self.balanceOf[addr] * (I - self.crv_integral_for[addr]) / 10 ** 18


@external
@nonreentrant('lock')
def claim_tokens(addr: address = msg.sender):
    """
    @notice Claim mintable CR
    @param addr Address to claim for
    """
    self._checkpoint(addr)
    ERC20(self.crv_token).transfer(addr, self.claimable_crv[addr])

    self.claimable_crv[addr] = 0


@external
def set_approve_deposit(addr: address, can_deposit: bool):
    """
    @notice Set whether `addr` can deposit tokens for `msg.sender`
    @param addr Address to set approval on
    @param can_deposit bool - can this account deposit for `msg.sender`?
    """
    self.approved_to_deposit[addr][msg.sender] = can_deposit


@external
@nonreentrant('lock')
def deposit(_value: uint256, addr: address = msg.sender):
    """
    @notice Deposit `_value` LP tokens
    @param _value Number of tokens to deposit
    @param addr Address to deposit for
    """
    assert not self.is_killed

    if addr != msg.sender:
        assert self.approved_to_deposit[msg.sender][addr], "Not approved"

    self._checkpoint(addr)

    if _value != 0:
        self.balanceOf[addr] += _value
        self.totalSupply += _value

        ERC20(self.lp_token).transferFrom(msg.sender, self, _value)
        LiquidityGauge(self.gauge).deposit(_value)

    log Deposit(addr, _value)


@external
@nonreentrant('lock')
def withdraw(_value: uint256):
    """
    @notice Withdraw `_value` LP tokens
    @param _value Number of tokens to withdraw
    """
    self._checkpoint(msg.sender)

    if _value != 0:
        self.balanceOf[msg.sender] -= _value
        self.totalSupply -= _value

        LiquidityGauge(self.gauge).withdraw(_value)
        ERC20(self.lp_token).transfer(msg.sender, _value)

    log Withdraw(msg.sender, _value)


@view
@external
def allowance(_owner : address, _spender : address) -> uint256:
    """
    @dev Function to check the amount of tokens that an owner allowed to a spender.
    @param _owner The address which owns the funds.
    @param _spender The address which will spend the funds.
    @return An uint256 specifying the amount of tokens still available for the spender.
    """
    return self.allowances[_owner][_spender]


@internal
def _transfer(_from: address, _to: address, _value: uint256):
    assert not self.is_killed

    self._checkpoint(_from)
    self._checkpoint(_to)

    if _value != 0:
        self.balanceOf[_from] -= _value
        self.balanceOf[_to] += _value

    log Transfer(_from, _to, _value)


@external
@nonreentrant('lock')
def transfer(_to : address, _value : uint256) -> bool:
    """
    @dev Transfer token for a specified address
    @param _to The address to transfer to.
    @param _value The amount to be transferred.
    """
    self._transfer(msg.sender, _to, _value)

    return True


@external
@nonreentrant('lock')
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    """
     @dev Transfer tokens from one address to another.
     @param _from address The address which you want to send tokens from
     @param _to address The address which you want to transfer to
     @param _value uint256 the amount of tokens to be transferred
    """
    _allowance: uint256 = self.allowances[_from][msg.sender]
    if _allowance != MAX_UINT256:
        self.allowances[_from][msg.sender] = _allowance - _value

    self._transfer(_from, _to, _value)

    return True


@external
def approve(_spender : address, _value : uint256) -> bool:
    """
    @notice Approve the passed address to transfer the specified amount of
            tokens on behalf of msg.sender
    @dev Beware that changing an allowance via this method brings the risk
         that someone may use both the old and new allowance by unfortunate
         transaction ordering. This may be mitigated with the use of
         {increaseAllowance} and {decreaseAllowance}.
         https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
    @param _spender The address which will transfer the funds
    @param _value The amount of tokens that may be transferred
    @return bool success
    """
    self.allowances[msg.sender][_spender] = _value
    log Approval(msg.sender, _spender, _value)

    return True


@external
def increaseAllowance(_spender: address, _added_value: uint256) -> bool:
    """
    @notice Increase the allowance granted to `_spender` by the caller
    @dev This is alternative to {approve} that can be used as a mitigation for
         the potential race condition
    @param _spender The address which will transfer the funds
    @param _added_value The amount of to increase the allowance
    @return bool success
    """
    allowance: uint256 = self.allowances[msg.sender][_spender] + _added_value
    self.allowances[msg.sender][_spender] = allowance

    log Approval(msg.sender, _spender, allowance)

    return True


@external
def decreaseAllowance(_spender: address, _subtracted_value: uint256) -> bool:
    """
    @notice Decrease the allowance granted to `_spender` by the caller
    @dev This is alternative to {approve} that can be used as a mitigation for
         the potential race condition
    @param _spender The address which will transfer the funds
    @param _subtracted_value The amount of to decrease the allowance
    @return bool success
    """
    allowance: uint256 = self.allowances[msg.sender][_spender] - _subtracted_value
    self.allowances[msg.sender][_spender] = allowance

    log Approval(msg.sender, _spender, allowance)

    return True


@external
def kill_me():
    assert msg.sender == self.admin
    self.is_killed = not self.is_killed


@external
def commit_transfer_ownership(addr: address):
    """
    @notice Transfer ownership of GaugeController to `addr`
    @param addr Address to have ownership transferred to
    """
    assert msg.sender == self.admin  # dev: admin only
    self.future_admin = addr
    log CommitOwnership(addr)


@external
def apply_transfer_ownership():
    """
    @notice Apply pending ownership transfer
    """
    assert msg.sender == self.admin  # dev: admin only
    _admin: address = self.future_admin
    assert _admin != ZERO_ADDRESS  # dev: admin not set
    self.admin = _admin
    log ApplyOwnership(_admin)
