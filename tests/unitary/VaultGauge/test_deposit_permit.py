import pytest
from eip712.messages import EIP712Message

class Permit(EIP712Message):
    _name_: "bytes32"
    _version_: "bytes32"
    _chainId_: "uint256"
    _verifyingContract_: "address"

    owner: "address"
    spender: "address"
    value: "uint256"
    nonce: "uint256"
    deadline: "uint256"

def test_permit(local, lixir_vault, vault_gauge, web3, chain):
    deadline = chain.time() + 86400
    message = Permit(
        _name_=web3.keccak(text=lixir_vault.name()),
        _version_=web3.keccak(text='1'),
        _chainId_=1337,
        _verifyingContract_=lixir_vault.address,

        owner=local.address,
        spender=vault_gauge.address,
        value=100,
        nonce=0,
        deadline=deadline
    )

    signed = local.sign_message(message)

    lixir_vault.deposit(10**6, 10**6, 0, 0, local.address, deadline, {"from": local})
    vault_gauge.deposit(10**6, local.address, deadline, signed.v, signed.r, signed.s)

    assert 1 == 0

