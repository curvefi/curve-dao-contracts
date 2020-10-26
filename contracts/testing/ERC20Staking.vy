"""
@notice Mock staking ERC20 for testing
"""

# @version 0.2.4

event Transfer:
    _from: indexed(address)
    _to: indexed(address)
    _value: uint256

event Approval:
    _owner: indexed(address)
    _spender: indexed(address)
    _value: uint256


name: public(String[64])
symbol: public(String[32])
decimals: public(uint256)
balances: public(HashMap[address, uint256])
allowances: HashMap[address, HashMap[address, uint256]]
total_supply: uint256
interest: decimal


@external
def __init__(_name: String[64], _symbol: String[32], _decimals: uint256):
    self.name = _name
    self.symbol = _symbol
    self.decimals = _decimals
    self.interest = 1.0


@external
@view
def totalSupply() -> uint256:
    return convert(convert(self.total_supply, decimal) * self.interest, uint256)


@external
@view
def balanceOf(_address: address) -> uint256:
    return convert(convert(self.balances[_address], decimal) * self.interest, uint256)


@external
@view
def allowance(_owner : address, _spender : address) -> uint256:
    return self.allowances[_owner][_spender]


@external
def transfer(_to : address, _value : uint256) -> bool:
    self.balances[msg.sender] -= _value
    self.balances[_to] += _value
    log Transfer(msg.sender, _to, _value)
    return True


@external
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    self.balances[_from] -= _value
    self.balances[_to] += _value
    self.allowances[_from][msg.sender] -= _value
    log Transfer(_from, _to, _value)
    return True


@external
def approve(_spender : address, _value : uint256) -> bool:
    self.allowances[msg.sender][_spender] = _value
    log Approval(msg.sender, _spender, _value)
    return True


@external
def _mint_for_testing(_value: uint256):
    self.total_supply += _value
    self.balances[msg.sender] += _value
    log Transfer(ZERO_ADDRESS, msg.sender, _value)

@external
def _set_interest(_value: decimal):
    self.interest = _value