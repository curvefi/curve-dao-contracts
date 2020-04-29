# The contract which controls gauges and issuance of coins through those

admin: address  # Can and will be a smart contract
token: address  # CRV token

# Gauge parameters
# All numbers are "fixed point" on the basis of 1e18
n_gauge_types: public(int128)
n_gauges: public(int128)

gauges: public(map(int128, address))
gauge_types: public(map(address, int128))
gauge_weights: public(map(address, uint256))
gauge_relative_weights: public(map(address, uint256))

type_weights: public(map(int128, uint256))
total_weight: public(uint256)


@public
def __init__(token_address: address):
    self.admin = msg.sender
    self.token = token_address
    self.n_gauge_types = 0
    self.n_gauges = 0
    self.total_weight = 0


@public
def transfer_ownership(addr: address):
    assert msg.sender == self.admin
    self.admin = addr


@public
def add_type():
    assert msg.sender == self.admin


@public
def add_gauge(addr: address, gauge_type: int128, weight: uint256 = 0):
    assert msg.sender == self.admin


@public
def change_type_weight(type_id: int128, weight: uint256):
    assert msg.sender == self.admin


@public
def change_gauge_weight(addr: address, weight: uint256):
    assert msg.sender == self.admin
