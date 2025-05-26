# @version 0.3.10
"""
@title Curve Crypto Pool Proxy
@author Curve Finance
@license MIT
@notice Used to control Custom Cryptoswap Pools
"""

from vyper.interfaces import ERC20

interface Burner:
    def burn(_coin: ERC20) -> bool: payable

interface Curve:
    def claim_admin_fees(): nonpayable
    def commit_transfer_ownership(_owner: address): nonpayable
    def accept_transfer_ownership(): nonpayable
    def apply_transfer_ownership(): nonpayable
    def revert_transfer_ownership(): nonpayable
    def commit_new_parameters(
        _new_mid_fee: uint256,
        _new_out_fee: uint256,
        _new_admin_fee: uint256,
        _new_fee_gamma: uint256,
        _new_price_threshold: uint256,
        _new_adjustment_step: uint256,
        _new_ma_half_time: uint256
    ): nonpayable
    def revert_new_parameters(): nonpayable
    def apply_new_parameters(): nonpayable
    def ramp_A_gamma(future_A: uint256, future_gamma: uint256, future_time: uint256): nonpayable
    def stop_ramp_A_gamma(): nonpayable
    def set_admin_fee_receiver(_admin_fee_receiver: address): nonpayable
    def set_aave_referral(referral_code: uint256): nonpayable
    def donate_admin_fees(): nonpayable
    def kill_me(): nonpayable
    def unkill_me(): nonpayable


MAX_COINS: constant(int128) = 8

event CommitAdmins:
    ownership_admin: address
    parameter_admin: address
    emergency_admin: address

event ApplyAdmins:
    ownership_admin: address
    parameter_admin: address
    emergency_admin: address

event SetBurner:
    coin: ERC20
    burner: Burner


ETH_ADDRESS: constant(address) = 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE

ownership_admin: public(address)
parameter_admin: public(address)
emergency_admin: public(address)

future_ownership_admin: public(address)
future_parameter_admin: public(address)
future_emergency_admin: public(address)

burner: public(Burner)

# pool -> caller -> can call `donate_admin_fees`
donate_approval: public(HashMap[Curve, HashMap[address, bool]])

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


@external
@nonreentrant('lock')
def set_burner(_burner: Burner):
    """
    @param _burner Burner contract address
    """
    assert msg.sender == self.ownership_admin, "Access denied"
    self.burner = _burner


@external
@nonreentrant('lock')
def withdraw_admin_fees(_pool: Curve):
    """
    @notice Withdraw admin fees from `_pool`
    @param _pool Pool address to withdraw admin fees from
    """
    _pool.claim_admin_fees()


@external
@nonreentrant('lock')
def withdraw_many(_pools: Curve[20]):
    """
    @notice Withdraw admin fees from multiple pools
    @param _pools List of pool address to withdraw admin fees from
    """
    for pool in _pools:
        if pool == empty(Curve):
            break
        pool.claim_admin_fees()


@internal
def _burn(_coin: ERC20):
    burner: Burner = self.burner
    value: uint256 = 0
    if _coin.address == ETH_ADDRESS:
        value = self.balance
    elif _coin.allowance(self, burner.address) < max_value(uint256) / 2:
        assert _coin.approve(burner.address, max_value(uint256), default_return_value=True)

    burner.burn(_coin, value=value)  # dev: should implement burn()


@external
@nonreentrant('burn')
def burn(_coin: ERC20):
    """
    @notice Burn accrued `_coin` via a preset burner
    @param _coin Coin address
    """
    self._burn(_coin)


@external
@nonreentrant('burn')
def burn_many(_coins: ERC20[20]):
    """
    @notice Burn accrued admin fees from multiple coins
    @param _coins List of coin addresses
    """
    for coin in _coins:
        if coin == empty(ERC20):
            break
        self._burn(coin)


@external
@nonreentrant('lock')
def kill_me(_pool: address):
    """
    @notice Pause the pool `_pool` - only remove_liquidity will be callable
    @param _pool Pool address to pause
    """
    assert msg.sender == self.emergency_admin, "Access denied"
    Curve(_pool).kill_me()


@external
@nonreentrant('lock')
def unkill_me(_pool: address):
    """
    @notice Unpause the pool `_pool`, re-enabling all functionality
    @param _pool Pool address to unpause
    """
    assert msg.sender == self.emergency_admin or msg.sender == self.ownership_admin, "Access denied"
    Curve(_pool).unkill_me()


@external
@nonreentrant('lock')
def commit_transfer_ownership(_pool: Curve, new_owner: address):
    """
    @notice Transfer ownership for `_pool` pool to `new_owner` address
    @param _pool Pool which ownership is to be transferred
    @param new_owner New pool owner address
    """
    assert msg.sender == self.ownership_admin, "Access denied"
    _pool.commit_transfer_ownership(new_owner)


@external
@nonreentrant('lock')
def apply_transfer_ownership(_pool: Curve):
    """
    @notice Apply transferring ownership of `_pool`
    @param _pool Pool address
    """
    _pool.apply_transfer_ownership()


@external
@nonreentrant('lock')
def accept_transfer_ownership(_pool: Curve):
    """
    @notice Apply transferring ownership of `_pool`
    @param _pool Pool address
    """
    _pool.accept_transfer_ownership()


@external
@nonreentrant('lock')
def revert_transfer_ownership(_pool: Curve):
    """
    @notice Revert commited transferring ownership for `_pool`
    @param _pool Pool address
    """
    assert msg.sender in [self.ownership_admin, self.emergency_admin], "Access denied"
    _pool.revert_transfer_ownership()


@external
@nonreentrant('lock')
def commit_new_parameters(
    _pool: Curve,
    _new_mid_fee: uint256,
    _new_out_fee: uint256,
    _new_admin_fee: uint256,
    _new_fee_gamma: uint256,
    _new_allowed_extra_profit: uint256,
    _new_adjustment_step: uint256,
    _new_ma_half_time: uint256,
):
    """
    @notice Commit new parameters for `_pool`, A: `amplification`, fee: `new_fee` and admin fee: `new_admin_fee`
    @param _pool Pool address
    @param _new_mid_fee New mid fee, less than or equal to `_new_out_fee`
    @param _new_out_fee New out fee, greater than MIN_FEE and less than MAX_FEE 
    @param _new_admin_fee New admin fee, less than MAX_ADMIN_FEE
    @param _new_fee_gamma New fee gamma, within the bounds of [1, 2**100]
    @param _new_allowed_extra_profit New allowed extra profit
    @param _new_adjustment_step New adjustment step
    @param _new_ma_half_time New MA half time, less than 7 days 
    """
    assert msg.sender == self.parameter_admin, "Access denied"
    _pool.commit_new_parameters(
        _new_mid_fee,
        _new_out_fee,
        _new_admin_fee,
        _new_fee_gamma,
        _new_allowed_extra_profit,
        _new_adjustment_step,
        _new_ma_half_time
    )  # dev: if implemented by the pool


@external
@nonreentrant('lock')
def apply_new_parameters(_pool: Curve):
    """
    @notice Apply new parameters for `_pool` pool
    @dev Only callable by an EOA
    @param _pool Pool address
    """
    assert msg.sender == tx.origin
    _pool.apply_new_parameters()  # dev: if implemented by the pool


@external
@nonreentrant('lock')
def revert_new_parameters(_pool: Curve):
    """
    @notice Revert committed new parameters for `_pool` pool
    @param _pool Pool address
    """
    assert msg.sender in [self.ownership_admin, self.parameter_admin, self.emergency_admin], "Access denied"
    _pool.revert_new_parameters()  # dev: if implemented by the pool


@external
@nonreentrant('lock')
def ramp_A_gamma(_pool: Curve, _future_A: uint256, _future_gamma: uint256, _future_time: uint256):
    """
    @notice Start gradually increasing A and gamma of `_pool` reaching `_future_A` and `_future_gamma` at `_future_time` time
    @param _pool Pool address
    @param _future_A Future A
    @param _future_time Future time
    """
    assert msg.sender == self.parameter_admin, "Access denied"
    _pool.ramp_A_gamma(_future_A, _future_gamma, _future_time)


@external
@nonreentrant('lock')
def stop_ramp_A_gamma(_pool: Curve):
    """
    @notice Stop gradually increasing A and gamma of `_pool`
    @param _pool Pool address
    """
    assert msg.sender in [self.parameter_admin, self.emergency_admin], "Access denied"
    _pool.stop_ramp_A_gamma()


@external
def set_admin_fee_receiver(_pool: Curve, _admin_fee_receiver: address):
    """
    @param _pool Pool address
    @param _admin_fee_receiver Contract receiving admin fees
    """
    assert msg.sender == self.ownership_admin, "Access denied"
    _pool.set_admin_fee_receiver(_admin_fee_receiver)


@external
@nonreentrant('lock')
def set_aave_referral(_pool: Curve, referral_code: uint256):
    """
    @notice Set Aave referral for underlying tokens of `_pool` to `referral_code`
    @param _pool Pool address
    @param referral_code Aave referral code
    """
    assert msg.sender == self.ownership_admin, "Access denied"
    _pool.set_aave_referral(referral_code)  # dev: if implemented by the pool


@external
def set_donate_approval(_pool: Curve, _caller: address, _is_approved: bool):
    """
    @notice Set approval of `_caller` to donate admin fees for `_pool`
    @param _pool Pool address
    @param _caller Address to set approval for
    @param _is_approved Approval status
    """
    assert msg.sender == self.ownership_admin, "Access denied"

    self.donate_approval[_pool][_caller] = _is_approved


@external
@nonreentrant('lock')
def donate_admin_fees(_pool: Curve):
    """
    @notice Donate admin fees of `_pool` pool
    @param _pool Pool address
    """
    if msg.sender != self.ownership_admin:
        assert self.donate_approval[_pool][msg.sender], "Access denied"

    _pool.donate_admin_fees()  # dev: if implemented by the pool
