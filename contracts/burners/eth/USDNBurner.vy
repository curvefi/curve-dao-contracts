# @version 0.2.7
"""
@title USDN Burner
@notice Return 50% of USDN to pool LPs, convert remaining to 3CRV
"""

from vyper.interfaces import ERC20

interface PoolProxy:
    def withdraw_admin_fees(_pool: address): nonpayable
    def donate_admin_fees(_pool: address): nonpayable


interface RegistrySwap:
    def exchange(
        _poool: address,
        _from: address,
        _to: address,
        _amount: uint256,
        _expected: uint256,
        _receiver: address,
    ) -> uint256: payable

interface AddressProvider:
    def get_address(_id: uint256) -> address: view


ADDRESS_PROVIDER: constant(address) = 0x0000000022D53366457F9d5E68Ec105046FC4383
TRIPOOL_LP: constant(address) = 0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490
USDN_POOL: constant(address) = 0x0f9cb53Ebe405d49A0bbdBD291A65Ff571bC83e1
USDN: constant(address) = 0x674C6Ad92Fd080e4004b2312b45f796a192D27a0

is_approved: HashMap[address, bool]

receiver: public(address)
recovery: public(address)
pool_proxy: public(address)

is_killed: public(bool)

owner: public(address)
emergency_owner: public(address)
future_owner: public(address)
future_emergency_owner: public(address)


@external
def __init__(_pool_proxy: address, _receiver: address, _recovery: address, _owner: address, _emergency_owner: address):
    """
    @notice Contract constructor
    @param _receiver Address that converted tokens are transferred to.
                     Should be set to an `UnderlyingBurner` deployment.
    @param _recovery Address that tokens are transferred to during an
                     emergency token recovery.
    @param _owner Owner address. Can kill the contract, recover tokens
                  and modify the recovery address.
    @param _emergency_owner Emergency owner address. Can kill the contract
                            and recover tokens.
    """
    self.pool_proxy = _pool_proxy
    self.receiver = _receiver
    self.recovery = _recovery
    self.owner = _owner
    self.emergency_owner = _emergency_owner


@payable
@external
def burn(_coin: address) -> bool:
    """
    @notice Swap `_coin` for 3CRV and transfer to the fee distributor
    @param _coin Address of the coin being swapped
    @return bool success
    """
    assert not self.is_killed  # dev: is killed
    assert _coin == USDN  # dev: only USDN

    # transfer coins from caller
    amount: uint256 = ERC20(USDN).balanceOf(msg.sender)
    if amount != 0:
        ERC20(USDN).transferFrom(msg.sender, self, amount)

    # get actual balance in case of transfer fee or pre-existing balance
    amount = ERC20(USDN).balanceOf(self)

    if amount > 1:
        # withdraw any pending fees from USDN pool
        PoolProxy(self.pool_proxy).withdraw_admin_fees(USDN_POOL)

        # transfer 50% of USDN back into the pool
        ERC20(USDN).transfer(USDN_POOL, amount / 2)

        # donate tranferred USDN to LPs
        PoolProxy(self.pool_proxy).donate_admin_fees(USDN_POOL)

        # swap remaining USDN for 3CRV and transfer to fee distributor
        amount = ERC20(USDN).balanceOf(self)
        registry_swap: address = AddressProvider(ADDRESS_PROVIDER).get_address(2)
        if not self.is_approved[registry_swap]:
            ERC20(USDN).approve(registry_swap, MAX_UINT256)
            self.is_approved[registry_swap] = True

        RegistrySwap(registry_swap).exchange(USDN_POOL, USDN, TRIPOOL_LP, amount, 0, self.receiver)

    return True


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
        concat(
            method_id("transfer(address,uint256)"),
            convert(self.recovery, bytes32),
            convert(amount, bytes32),
        ),
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
def set_pool_proxy(_pool_proxy: address) -> bool:
    """
    @notice Set the pool proxy address
    @param _pool_proxy Pool proxy address
    @return bool success
    """
    assert msg.sender == self.owner  # dev: only owner
    self.pool_proxy = _pool_proxy

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
