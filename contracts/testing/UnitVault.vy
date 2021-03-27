# @version 0.2.11

from vyper.interfaces import ERC20

# asset -> owner -> amount
collaterals: public(HashMap[address, HashMap[address, uint256]])

token: address


@external
def set_token(_token: address):
    self.token = _token

@external
def deposit(_amount: uint256):
    ERC20(self.token).transferFrom(msg.sender, self, _amount)
    self.collaterals[self.token][msg.sender] += _amount


@external
def withdraw(_amount: uint256):
    self.collaterals[self.token][msg.sender] -= _amount
    ERC20(self.token).transfer(msg.sender, _amount)


@external
def liquidate(_user: address, _amount: uint256):
    total: uint256 = self.collaterals[self.token][_user]
    self.collaterals[self.token][_user] = 0
    ERC20(self.token).transfer(_user, total - _amount)
    ERC20(self.token).transfer(msg.sender, _amount)
