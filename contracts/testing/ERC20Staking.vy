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
last_interest: public(HashMap[address, uint256])
interests: decimal[100000000000000000000000000000]
interests_len: uint256
allowances: HashMap[address, HashMap[address, uint256]]
total_supply: uint256
interest: decimal


@external
def __init__(_name: String[64], _symbol: String[32], _decimals: uint256):
    self.name = _name
    self.symbol = _symbol
    self.decimals = _decimals
    self.interests[0] = 1.0
    self.interests_len = 1


@external
@view
def totalSupply() -> uint256:
    return self.total_supply


@external
@view
def balanceOf(_address: address) -> uint256:
    return convert(convert(self.balances[_address], decimal) * self.interests[self.interests_len - 1] / self.interests[self.last_interest[_address]], uint256)


@external
@view
def allowance(_owner : address, _spender : address) -> uint256:
    return self.allowances[_owner][_spender]


@external
def transfer(_to : address, _value : uint256) -> bool:
    sender_balance: uint256 = convert(convert(self.balances[msg.sender], decimal) * self.interests[self.interests_len - 1] / self.interests[self.last_interest[msg.sender]], uint256)
    self.balances[msg.sender] = sender_balance - _value
    self.last_interest[msg.sender] = self.interests_len - 1

    recipient_balance: uint256 = convert(convert(self.balances[_to], decimal) * self.interests[self.interests_len - 1] / self.interests[self.last_interest[_to]], uint256)
    self.balances[_to] = recipient_balance + _value
    self.last_interest[_to] = self.interests_len - 1

    log Transfer(msg.sender, _to, _value)
    return True


@external
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    sender_balance: uint256 = convert(convert(self.balances[_from], decimal) * self.interests[self.interests_len - 1] / self.interests[self.last_interest[_from]], uint256)
    self.balances[_from] = sender_balance - _value
    self.last_interest[_from] = self.interests_len - 1

    recipient_balance: uint256 = convert(convert(self.balances[_to], decimal) * self.interests[self.interests_len - 1] / self.interests[self.last_interest[_to]], uint256)
    self.balances[_to] = recipient_balance + _value
    self.last_interest[_to] = self.interests_len - 1

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
    balance_msg: uint256 = convert(convert(self.balances[msg.sender], decimal) * self.interests[self.interests_len - 1] / self.interests[self.last_interest[msg.sender]], uint256)
    self.balances[msg.sender] = balance_msg + _value
    self.last_interest[msg.sender] = self.interests_len - 1
    log Transfer(ZERO_ADDRESS, msg.sender, _value)

@external
def reward(_value: uint256):
    self.interests_len += 1
    self.interests[self.interests_len - 1] =  self.interests[self.interests_len - 2] * (1.0 + convert(_value, decimal) / convert(self.total_supply, decimal))