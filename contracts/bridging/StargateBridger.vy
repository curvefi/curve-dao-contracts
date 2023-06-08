# @version 0.3.9
"""
@title Stargate Bridger
@author Curve Finance
@license MIT
"""
from vyper.interfaces import ERC20


interface IStargateRouter:
    def quoteLayerZeroFee(
        dst_chain_id: uint16,
        function_type: uint8,
        to: Bytes[256],
        payload: Bytes[256],
        txn_params: TxnParams,
    ) -> uint256[2]: view
    def swap(
        dst_chain_id: uint16,
        src_pool_id: uint256,
        dst_pool_id: uint256,
        refund_address: address,
        amount: uint256,
        min_amount: uint256,
        txn_params: TxnParams,
        to: Bytes[256],
        payload: Bytes[256],
    ): payable


event SetRootReceiver:
    receiver: indexed(address)

event CommitOwnership:
    future_owner: indexed(address)

event AcceptOwnership:
    owner: indexed(address)


struct TxnParams:
    gas: uint256
    amount: uint256
    to: Bytes[256]


ROUTER: public(immutable(address))


receiver: public(address)

owner: public(address)
future_owner: public(address)


@external
def __init__(receiver: address, router: address):
    ROUTER = router
    
    self.owner = msg.sender
    self.receiver = receiver

    log SetRootReceiver(receiver)


@payable
@external
def __default__():
    assert len(msg.data) == 0


@external
def bridge(token: address):
    assert msg.sender == self.owner

    amount: uint256 = ERC20(token).balanceOf(self)
    receiver: address = self.receiver
    fee: uint256[2] = IStargateRouter(ROUTER).quoteLayerZeroFee(
        101, 1, _abi_encode(receiver), b"", TxnParams({gas: 0, amount: 0, to: b""})
    )


@external
def set_root_receiver(receiver: address):
    assert msg.sender == self.owner

    self.receiver = receiver
    log SetRootReceiver(receiver)


@external
def commit_transfer_ownership(future_owner: address):
    assert msg.sender == self.owner

    self.future_owner = future_owner
    log CommitOwnership(future_owner)


@external
def accept_transfer_ownership():
    assert msg.sender == self.future_owner

    self.owner = msg.sender
    log AcceptOwnership(msg.sender)
