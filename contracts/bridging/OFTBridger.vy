# @version 0.3.7
"""
@title OFT Bridger
@author Curve Finance
@license MIT
"""
from vyper.interfaces import ERC20


interface ProxyOFT:
    def estimateSendFee(
        destination: uint16,
        to: bytes32,
        amount: uint256,
        use_zero: bool,
        adapter_params: Bytes[128],
    ) -> uint256: view
    def sendFrom(
        origin: address,
        destination: uint16,
        to: bytes32,
        amount: uint256,
        call_params: CallParams
    ): payable


event CommitOwnership:
    owner: address

event AcceptOwnership:
    owner: address

event AssetBridged:
    token: indexed(address)
    amount: uint256


struct CallParams:
    refund: address
    zero_payer: address
    adapter_params: Bytes[128]


ETH_CHAIN_ID: constant(uint16) = 101


PROXY_OFT: public(immutable(address))
TOKEN: public(immutable(address))


receiver: public(address)

owner: public(address)
future_owner: public(address)


@external
def __init__(proxy_oft: address, receiver: address, token: address):
    self.owner = msg.sender
    self.receiver = receiver

    PROXY_OFT = proxy_oft
    TOKEN = token

    log AcceptOwnership(msg.sender)


@payable
@external
def __default__():
    assert len(msg.data) == 0


@external
def bridge(coin: address) -> bool:
    assert msg.sender == self.owner and coin == TOKEN

    amount: uint256 = ERC20(coin).balanceOf(self)
    if amount == 0:
        amount = ERC20(coin).balanceOf(msg.sender)
        assert ERC20(coin).transferFrom(msg.sender, self, amount)
    
    receiver: address = self.receiver
    adapter_params: Bytes[128] = concat(
        b"\x00\x02",
        convert(100_000, bytes32),
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        convert(receiver, bytes32)
    )

    fee: uint256 = ProxyOFT(PROXY_OFT).estimateSendFee(
        ETH_CHAIN_ID, convert(receiver, bytes32), amount, False, adapter_params,
    )
    assert ERC20(coin).approve(PROXY_OFT, amount)

    ProxyOFT(PROXY_OFT).sendFrom(
        self,
        ETH_CHAIN_ID,
        convert(receiver, bytes32),
        amount,
        CallParams({
            refund: self,
            zero_payer: empty(address),
            adapter_params: adapter_params,
        }),
        value=fee
    )

    log AssetBridged(coin, amount)
    return True


@external
def commit_transfer_ownership(future_owner: address):
    assert msg.sender == self.owner

    self.future_owner = future_owner
    log CommitOwnership(future_owner)


@external
def accept_transfer_ownership():
    assert msg.sender == self.future_owner

    self.future_owner = msg.sender
    log AcceptOwnership(msg.sender)


@external
def recover(coin: address):
    assert msg.sender == self.owner
    
    if coin == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        raw_call(msg.sender, b"", value=self.balance)
    else:
        assert ERC20(coin).transfer(msg.sender, ERC20(coin).balanceOf(self))


@external
def set_root_receiver(receiver: address):
    assert msg.sender == self.owner
    assert receiver != empty(address)

    self.receiver = receiver
