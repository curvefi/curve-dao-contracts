# @version 0.2.4
"""
@title Staking Burner
@author Curve Finance
@license MIT
@notice Used for share profit
"""


from vyper.interfaces import ERC20


interface Pool:
    def coins(i: uint256) -> address: view
    def exchange(i: int128, j: int128, dx: uint256, min_dy: uint256): nonpayable


interface Gauge:
    def integrate_fraction(_address: address) -> uint256: view
    def integrate_inv_supply_of(_address: address) -> uint256: view


SHARE: constant(decimal) = 0.5


pool: public(address)
pool_proxy: public(address)
ve_holder: public(address)
burned: public(uint256)
burned_of: public(HashMap[address, uint256])
gauge: public(address)
integrate_fraction: public(HashMap[address, uint256])
integrate_inv_supply_of: public(HashMap[address, uint256])


@external
def __init__(_ve_holder: address, _pool: address, _pool_proxy: address, _gauge: address):
    self.ve_holder = _ve_holder
    self.pool = _pool
    self.pool_proxy = _pool_proxy
    self.gauge = _gauge


@external
@nonreentrant('lock')
def burn_coin(_coin: address) -> bool:
    last_fraction: uint256 = Gauge(self.gauge).integrate_fraction(msg.sender)
    holder_fraction: uint256 = self.integrate_fraction[msg.sender]
    assert holder_fraction < last_fraction, "Already burned"

    potential_profit: uint256 = ERC20(_coin).balanceOf(self.pool_proxy) + self.burned
    ve_profit: uint256 = convert(convert(potential_profit, decimal) * SHARE, uint256)
    lp_profit: uint256 = potential_profit - ve_profit

    last_integrate_inv: uint256 = Gauge(self.gauge).integrate_inv_supply_of(msg.sender)
    holder_last_integrate_inv: uint256 = self.integrate_inv_supply_of[msg.sender]

    burn_balance: uint256 = lp_profit * (last_fraction - holder_fraction) / (last_integrate_inv - holder_last_integrate_inv) - self.burned_of[msg.sender] 
    ERC20(_coin).transferFrom(self.pool_proxy , msg.sender, burn_balance)
    self.burned += burn_balance
    self.burned_of[msg.sender] += burn_balance

    self.integrate_fraction[msg.sender] = last_fraction
    self.integrate_inv_supply_of[msg.sender] = last_integrate_inv

    ve_profit -= self.burned_of[self.ve_holder]
    if ve_profit > 0:
        self.burned += ve_profit
        self.burned_of[self.ve_holder] += ve_profit

        if Pool(self.pool).coins(0) == _coin:
            # Pool(self.pool).exchange(0, 1, ve_profit, 0)
            second_coin: address =  Pool(self.pool).coins(1)
            second_coin_balance: uint256 = ERC20(second_coin).balanceOf(self)
            ERC20(second_coin).transfer(self.ve_holder, second_coin_balance)
        else:
            second_coin: address =  Pool(self.pool).coins(0)
            second_coin_balance: uint256 = ERC20(second_coin).balanceOf(self)
            ERC20(_coin).approve(self.pool, 2**128 - 1)
            ERC20(second_coin).approve(self.pool, 2**128 - 1)
            Pool(self.pool).exchange(1, 0, ve_profit, 0)
            ERC20(second_coin).transfer(self.ve_holder, second_coin_balance)

    return True


@external
@view
def claim_tokens(_coin: address) -> uint256:
    last_fraction: uint256 = Gauge(self.gauge).integrate_fraction(msg.sender)
    holder_fraction: uint256 = self.integrate_fraction[msg.sender]
    assert holder_fraction < last_fraction, "Already burned"

    potential_profit: uint256 = ERC20(_coin).balanceOf(self.pool_proxy) + self.burned
    ve_profit: uint256 = convert(convert(potential_profit, decimal) * SHARE, uint256)
    lp_profit: uint256 = potential_profit - ve_profit

    last_integrate_inv: uint256 = Gauge(self.gauge).integrate_inv_supply_of(msg.sender)
    holder_last_integrate_inv: uint256 = self.integrate_inv_supply_of[msg.sender]

    burn_balance: uint256 = lp_profit * (last_fraction - holder_fraction) / (last_integrate_inv - holder_last_integrate_inv) - self.burned_of[msg.sender] 
    return burn_balance