# @version 0.2.7
"""
@title Curve StableSwap Proxy
@author Curve Finance
@license MIT
"""

# TODO idk if we want the VaultProxy to be have the pauser role?? we could...
# TODO could give this contract the power to set the strategy?
# TODO could give this contract the power to set fees??
# this contract will be the fee_setter_role and will be the fee_to in the registry

interface Burner:
    def burn(_coin: address) -> bool: payable

interface LixirVault:
    def setPerformanceFee(newFee: uint256): nonpayable # actually a uint24 but vyper is retarded


event CommitAdmins:
    ownership_admin: address
    parameter_admin: address
    emergency_admin: address

event ApplyAdmins:
    ownership_admin: address
    parameter_admin: address
    emergency_admin: address

event AddBurner:
    burner: address


ownership_admin: public(address)
parameter_admin: public(address)
emergency_admin: public(address)

future_ownership_admin: public(address)
future_parameter_admin: public(address)
future_emergency_admin: public(address)

burners: public(HashMap[address, address])
burner_kill: public(bool)


@external
def __init__(
    _ownership_admin: address,
    _parameter_admin: address,
    _emergency_admin: address
):
    self.ownership_admin = _ownership_admin
    self.parameter_admin = _parameter_admin
    self.emergency_admin = _emergency_admin


@payable
@external
def __default__():
    # required to receive ETH fees
    pass


@external
def commit_set_admins(_o_admin: address, _p_admin: address, _e_admin: address):
    """
    @notice Set ownership admin to `_o_admin`, parameter admin to `_p_admin` and emergency admin to `_e_admin`
    @param _o_admin Ownership admin
    @param _p_admin Parameter admin
    @param _e_admin Emergency admin
    """
    assert msg.sender == self.ownership_admin, "Access denied"

    self.future_ownership_admin = _o_admin
    self.future_parameter_admin = _p_admin
    self.future_emergency_admin = _e_admin

    log CommitAdmins(_o_admin, _p_admin, _e_admin)


@external
def apply_set_admins():
    """
    @notice Apply the effects of `commit_set_admins`
    """
    assert msg.sender == self.ownership_admin, "Access denied"

    _o_admin: address = self.future_ownership_admin
    _p_admin: address = self.future_parameter_admin
    _e_admin: address = self.future_emergency_admin
    self.ownership_admin = _o_admin
    self.parameter_admin = _p_admin
    self.emergency_admin = _e_admin

    log ApplyAdmins(_o_admin, _p_admin, _e_admin)


@internal
def _set_burner(_coin: address, _burner: address):
    old_burner: address = self.burners[_coin]
    if _coin != 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        if old_burner != ZERO_ADDRESS:
            # revoke approval on previous burner
            response: Bytes[32] = raw_call(
                _coin,
                concat(
                    method_id("approve(address,uint256)"),
                    convert(old_burner, bytes32),
                    convert(0, bytes32),
                ),
                max_outsize=32,
            )
            if len(response) != 0:
                assert convert(response, bool)

        if _burner != ZERO_ADDRESS:
            # infinite approval for current burner
            response: Bytes[32] = raw_call(
                _coin,
                concat(
                    method_id("approve(address,uint256)"),
                    convert(_burner, bytes32),
                    convert(MAX_UINT256, bytes32),
                ),
                max_outsize=32,
            )
            if len(response) != 0:
                assert convert(response, bool)

    self.burners[_coin] = _burner

    log AddBurner(_burner)


@external
@nonreentrant('lock')
def set_burner(_coin: address, _burner: address):
    """
    @notice Set burner of `_coin` to `_burner` address
    @param _coin Token address
    @param _burner Burner contract address
    """
    assert msg.sender == self.ownership_admin, "Access denied"

    self._set_burner(_coin, _burner)


@external
@nonreentrant('lock')
def set_many_burners(_coins: address[20], _burners: address[20]):
    """
    @notice Set burner of `_coin` to `_burner` address
    @param _coins Token address
    @param _burners Burner contract address
    """
    assert msg.sender == self.ownership_admin, "Access denied"

    for i in range(20):
        coin: address = _coins[i]
        if coin == ZERO_ADDRESS:
            break
        self._set_burner(coin, _burners[i])


@external
@nonreentrant('burn')
def burn(_coin: address):
    """
    @notice Burn accrued `_coin` via a preset burner
    @dev Only callable by an EOA to prevent flashloan exploits
    @param _coin Coin address
    """
    assert tx.origin == msg.sender
    assert not self.burner_kill

    _value: uint256 = 0
    if _coin == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        _value = self.balance # TODO wtf is this???

    Burner(self.burners[_coin]).burn(_coin, value=_value)  # dev: should implement burn()


@external
@nonreentrant('burn')
def burn_many(_coins: address[20]):
    """
    @notice Burn accrued admin fees from multiple coins
    @dev Only callable by an EOA to prevent flashloan exploits
    @param _coins List of coin addresses
    """
    assert tx.origin == msg.sender
    assert not self.burner_kill

    for coin in _coins:
        if coin == ZERO_ADDRESS:
            break

        _value: uint256 = 0
        if coin == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
            _value = self.balance

        Burner(self.burners[coin]).burn(coin, value=_value)  # dev: should implement burn()


# @external
# @nonreentrant('lock')
# def kill_me(_pool: address):
#     """
#     @notice Pause the pool `_pool` - only remove_liquidity will be callable
#     @param _pool Pool address to pause
#     """
#     assert msg.sender == self.emergency_admin, "Access denied"
#     Curve(_pool).kill_me()


# @external
# @nonreentrant('lock')
# def unkill_me(_pool: address):
#     """
#     @notice Unpause the pool `_pool`, re-enabling all functionality
#     @param _pool Pool address to unpause
#     """
#     assert msg.sender == self.emergency_admin or msg.sender == self.ownership_admin, "Access denied"
#     Curve(_pool).unkill_me()


@external
def set_burner_kill(_is_killed: bool):
    """
    @notice Kill or unkill `burn` functionality
    @param _is_killed Burner kill status
    """
    assert msg.sender == self.emergency_admin or msg.sender == self.ownership_admin, "Access denied"
    self.burner_kill = _is_killed


# @external
# @nonreentrant('lock')
# def commit_new_fee(_pool: address, new_fee: uint256, new_admin_fee: uint256):
#     """
#     @notice Commit new fees for `_pool` pool, fee: `new_fee` and admin fee: `new_admin_fee`
#     @param _pool Pool address
#     @param new_fee New fee
#     @param new_admin_fee New admin fee
#     """
#     assert msg.sender == self.parameter_admin, "Access denied"
#     Curve(_pool).commit_new_fee(new_fee, new_admin_fee)


# @external
# @nonreentrant('lock')
# def apply_new_fee(_pool: address):
#     """
#     @notice Apply new fees for `_pool` pool
#     @param _pool Pool address
#     """
#     Curve(_pool).apply_new_fee()
