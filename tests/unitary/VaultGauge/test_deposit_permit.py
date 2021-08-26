import pytest
from eip712.messages import EIP712Message
import eth_abi
from brownie.convert import to_bytes

# almost certain this is correct construction because I got it fro
# one of the test cases in eip712.py
class Permit(EIP712Message):
    _name_: "string" = "Test Vault Token"
    _version_: "string"
    _chainId_: "uint256"
    _verifyingContract_: "address"

    owner: "address"
    spender: "address"
    value: "uint256"
    nonce: "uint256"
    deadline: "uint256"


def test_permit(local, lixir_vault, vault_gauge, web3, chain):
    lixir_vault.deposit(50, 50, 0, 0, local, 9999999999, {"from":local})

    message = Permit(
        _name_='Test Vault Token',
        _version_='1',
        _chainId_=lixir_vault.getChainId(),
        _verifyingContract_=lixir_vault.address,

        owner=local.address,
        spender=vault_gauge.address,
        value=100,
        nonce=0,
        deadline=9999999999
    )

    signed = local.sign_message(message)

    calldata = eth_abi.encode_single(
        "(uint256,uint8,bytes32,bytes32)",
        [
            9999999999,
            signed.v,
            to_bytes(signed.r),
            to_bytes(signed.s)
        ]
    ).hex()

    vault_gauge.deposit(100, local, calldata, {"from": local})
    
    assert lixir_vault.balanceOf(local) == 0
    assert lixir_vault.balanceOf(vault_gauge) == 100

