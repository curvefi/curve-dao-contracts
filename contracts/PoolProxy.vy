from vyper.interfaces import ERC20

interface Burner:
    def burn() -> bool: nonpayable
    def burn_eth() -> bool: payable
    def burn_coin(_coin: address)-> bool: nonpayable

interface Curve:
    def withdraw_admin_fees(): nonpayable
    def kill_me(): nonpayable
    def unkill_me(): nonpayable
    def commit_transfer_ownership(new_owner: address): nonpayable
    def apply_transfer_ownership(): nonpayable
    def revert_transfer_ownership(): nonpayable
    def commit_new_parameters(amplification: uint256, new_fee: uint256, new_admin_fee: uint256): nonpayable
    def apply_new_parameters(): nonpayable
    def revert_new_parameters(): nonpayable
    def commit_new_fee(new_fee: uint256, new_admin_fee: uint256): nonpayable
    def apply_new_fee(): nonpayable
    def ramp_A(_future_A: uint256, _future_time: uint256): nonpayable
    def stop_ramp_A(): nonpayable
    def set_aave_referral(referral_code: uint256): nonpayable
    def donate_admin_fees(): nonpayable


ownership_admin: public(address)
parameter_admin: public(address)
emergency_admin: public(address)
burners: public(HashMap[address, address])


@external
def __init__():
    self.ownership_admin = msg.sender
    self.parameter_admin = msg.sender
    self.emergency_admin = msg.sender


@external
def set_admins(_o_admin: address, _p_admin: address, _e_admin: address):
    assert msg.sender == self.ownership_admin, "Access denied"

    self.ownership_admin = _o_admin
    self.parameter_admin = _p_admin
    self.emergency_admin = _e_admin


@external
@nonreentrant('lock')
def set_burner(_token: address, _burner: address):
    assert msg.sender == self.ownership_admin, "Access denied"

    _old_burner: address = self.burners[_token]

    if _token != ZERO_ADDRESS:
        if _old_burner != ZERO_ADDRESS:
            ERC20(_token).approve(_old_burner, 0)
        if _burner != ZERO_ADDRESS:
            ERC20(_token).approve(_burner, MAX_UINT256)

    self.burners[_token] = _burner


@external
@nonreentrant('lock')
def withdraw_admin_fees(_pool: address):
    Curve(_pool).withdraw_admin_fees()


@external
@nonreentrant('lock')
def burn(_burner: address):
    Burner(_burner).burn()  # dev: should implement burn()


@external
@nonreentrant('lock')
def burn_coin(_coin: address):
    Burner(self.burners[_coin]).burn_coin(_coin)  # dev: should implement burn_coin()


@external
@payable
@nonreentrant('lock')
def burn_eth():
    Burner(self.burners[ZERO_ADDRESS]).burn_eth(value=self.balance)  # dev: should implement burn_eth()


@external
@nonreentrant('lock')
def kill_me(_pool: address):
    assert msg.sender == self.emergency_admin, "Access denied"
    Curve(_pool).kill_me()


@external
@nonreentrant('lock')
def unkill_me(_pool: address):
    assert msg.sender == self.emergency_admin or msg.sender == self.ownership_admin, "Access denied"
    Curve(_pool).unkill_me()


@external
@nonreentrant('lock')
def commit_transfer_ownership(_pool: address, new_owner: address):
    assert msg.sender == self.ownership_admin, "Access denied"
    Curve(_pool).commit_transfer_ownership(new_owner)


@external
@nonreentrant('lock')
def apply_transfer_ownership(_pool: address):
    Curve(_pool).apply_transfer_ownership()


@external
@nonreentrant('lock')
def revert_transfer_ownership(_pool: address):
    assert msg.sender == self.ownership_admin, "Access denied"
    Curve(_pool).revert_transfer_ownership()


@external
@nonreentrant('lock')
def commit_new_parameters(_pool: address,
                          amplification: uint256,
                          new_fee: uint256,
                          new_admin_fee: uint256):
    assert msg.sender == self.parameter_admin, "Access denied"
    Curve(_pool).commit_new_parameters(amplification, new_fee, new_admin_fee)  # dev: if implemented by the pool


@external
@nonreentrant('lock')
def apply_new_parameters(_pool: address):
    Curve(_pool).apply_new_parameters()  # dev: if implemented by the pool


@external
@nonreentrant('lock')
def revert_new_parameters(_pool: address):
    assert msg.sender == self.parameter_admin, "Access denied"
    Curve(_pool).revert_new_parameters()  # dev: if implemented by the pool


@external
@nonreentrant('lock')
def commit_new_fee(_pool: address, new_fee: uint256, new_admin_fee: uint256):
    assert msg.sender == self.parameter_admin, "Access denied"
    Curve(_pool).commit_new_fee(new_fee, new_admin_fee)


@external
@nonreentrant('lock')
def apply_new_fee(_pool: address):
    Curve(_pool).apply_new_fee()


@external
@nonreentrant('lock')
def ramp_A(_pool: address, _future_A: uint256, _future_time: uint256):
    assert msg.sender == self.parameter_admin, "Access denied"
    Curve(_pool).ramp_A(_future_A, _future_time)


@external
@nonreentrant('lock')
def stop_ramp_A(_pool: address):
    assert msg.sender == self.parameter_admin, "Access denied"
    Curve(_pool).stop_ramp_A()


@external
@nonreentrant('lock')
def set_aave_referral(_pool: address, referral_code: uint256):
    assert msg.sender == self.ownership_admin, "Access denied"
    Curve(_pool).set_aave_referral(referral_code)  # dev: if implemented by the pool


@external
@nonreentrant('lock')
def donate_admin_fees(_pool: address):
    assert msg.sender == self.ownership_admin, "Access denied"
    Curve(_pool).donate_admin_fees()  # dev: if implemented by the pool
