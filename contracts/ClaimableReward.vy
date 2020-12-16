# @version 0.2.4
"""
@title Claimable Reward
@author Curve Finance
@license MIT
@notice Used for share reward
"""


from vyper.interfaces import ERC20


interface Gauge:
    def integrate_fraction(_address: address) -> uint256: view
    def integrate_inv_supply_of(account: address) -> uint256: view
    def working_supply() -> uint256: view
    def working_balances(account: address) -> uint256: view


event CommitOwnership:
    admin: address

event ApplyOwnership:
    admin: address

event Deposit:
    coin: indexed(address)
    value: uint256

event ClaimStarted:
    coin: indexed(address)
    account: indexed(address)

event ClaimReward:
    to: indexed(address)
    value: uint256

event Withdrawal:
    coin: address
    value: uint256


INTEGRATE_INV_SUPPLY_FACTOR: constant(uint256) = 10 ** 18


owner: public(address)
future_owner: public(address)

gauge: public(address)
last_fraction: public(HashMap[address, HashMap[address, uint256]])
last_integrate_inv: public(HashMap[address, HashMap[address, uint256]])
claimable_accounts: public(HashMap[address, HashMap[address, bool]])
integrated_deposit: public(HashMap[address, uint256])
commited_deposit_for: public(HashMap[address, HashMap[address, uint256]])
current_working_supply: public(HashMap[address, uint256])


@external
def __init__(_gauge: address):
    """
    @notice Contract constructor
    @param _gauge Liquidity gauge contract address
    """
    self.gauge = _gauge
    self.owner = msg.sender


@view
@internal
def _claimable_tokens(_coin: address, account: address) -> uint256:
    total_balance: uint256 = ERC20(_coin).balanceOf(self)
    fraction: uint256 = Gauge(self.gauge).integrate_fraction(account)
    old_fraction: uint256 = self.last_fraction[_coin][account]
    integrate_inv: uint256 = Gauge(self.gauge).integrate_inv_supply_of(account)
    old_integrate_inv: uint256 = self.last_integrate_inv[_coin][account]
    working_supply: uint256 = max(self.current_working_supply[_coin], Gauge(self.gauge).working_supply())

    assert self.claimable_accounts[_coin][account], "claim is not allowed"

    if fraction == old_fraction or integrate_inv == old_integrate_inv or self.integrated_deposit[_coin] == self.commited_deposit_for[_coin][account]:
        return 0

    delta_fraction: uint256 = fraction - old_fraction
    delta_integrate_inv: uint256 = integrate_inv - old_integrate_inv

    claim_amount: uint256 = (self.integrated_deposit[_coin] - self.commited_deposit_for[_coin][account]) * INTEGRATE_INV_SUPPLY_FACTOR * delta_fraction / delta_integrate_inv / working_supply

    if claim_amount > total_balance:
        if total_balance * INTEGRATE_INV_SUPPLY_FACTOR * delta_fraction / delta_integrate_inv / working_supply > total_balance:
            return total_balance
        else:
            return total_balance * INTEGRATE_INV_SUPPLY_FACTOR * delta_fraction / delta_integrate_inv / working_supply

    return claim_amount


@view
@external
def claimable_tokens(_coin: address) -> uint256:
    """
    @notice Return amount of available _coin for claim
    @param _coin Address of ERC20 token for claim reward 
    """
    return self._claimable_tokens(_coin, msg.sender)


@external
@nonreentrant('lock')
def deposit(_coin: address, _value: uint256):
    """
    @notice Deposit _value of _coin available to claim for gauge holder users
    @param _coin Address of ERC20 token for claim reward 
    @param _value amount of _coin for claim reward 
    """
    assert _value > 0, "zero amount not allowed"
    assert ERC20(_coin).transferFrom(msg.sender, self, _value)
    self.current_working_supply[_coin] = Gauge(self.gauge).working_supply()
    self.integrated_deposit[_coin] += _value

    log Deposit(_coin, _value)


@external
@nonreentrant('lock')
def start_claiming(_coin: address):
    """
    @notice Allowes to participate in _coin claiming for caller, should be called after deposit lp tokens on gauge
    @param _coin Address of ERC20 token for claim reward 
    """
    assert Gauge(self.gauge).working_balances(msg.sender) > 0, "no lp tokens in gauge"
    assert not self.claimable_accounts[_coin][msg.sender], "claiming already started"

    self.claimable_accounts[_coin][msg.sender] = True
    self.last_fraction[_coin][msg.sender] = Gauge(self.gauge).integrate_fraction(msg.sender)
    self.last_integrate_inv[_coin][msg.sender] = Gauge(self.gauge).integrate_inv_supply_of(msg.sender)
    self.commited_deposit_for[_coin][msg.sender] = self.integrated_deposit[_coin]
    
    log ClaimStarted(_coin, msg.sender)


@external
@nonreentrant('lock')
def claim(_coin: address):
    """
    @notice Claims available reward in _coin to caller
    @param _coin Address of ERC20 token for claim reward
    """
    assert self.claimable_accounts[_coin][msg.sender], "claim is not allowed"

    available_amount: uint256 = self._claimable_tokens(_coin, msg.sender)
    assert available_amount > 0, "already claimed"

    ERC20(_coin).transfer(msg.sender, available_amount)
    self.last_integrate_inv[_coin][msg.sender] = Gauge(self.gauge).integrate_inv_supply_of(msg.sender)
    self.last_fraction[_coin][msg.sender] = Gauge(self.gauge).integrate_fraction(msg.sender)
    self.commited_deposit_for[_coin][msg.sender] = self.integrated_deposit[_coin]

    log ClaimReward(msg.sender, available_amount)


@external
@nonreentrant('lock')
def emergency_withdrawal(_coin: address):
    """
    @notice Emergency withdrawal for _coin amount from contract to owner
    @param _coin Address of ERC20 token for withdrawal
    """
    assert msg.sender == self.owner, "owner only"
    available_amount: uint256 = ERC20(_coin).balanceOf(self)
    assert available_amount > 0, "zero amount"
    assert ERC20(_coin).transfer(self.owner, available_amount)

    log Withdrawal(_coin, available_amount)


@external
def commit_transfer_ownership(addr: address):
    """
    @notice Transfer ownership of ClaimableReward to `addr`
    @param addr Address to have ownership transferred to
    """
    assert msg.sender == self.owner, "owner only"
    self.future_owner = addr
    log CommitOwnership(addr)


@external
def apply_transfer_ownership():
    """
    @notice Apply pending ownership transfer
    """
    assert msg.sender == self.owner, "owner only"
    _owner: address = self.future_owner
    assert _owner != ZERO_ADDRESS, "owner not set"
    self.owner = _owner
    log ApplyOwnership(_owner)