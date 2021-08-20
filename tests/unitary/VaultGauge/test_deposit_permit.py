import pytest
from eip712.messages import EIP712Message


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
    deadline = chain.time() + 86400
    message = Permit(
        _name_=lixir_vault.name(),
        _version_='1',
        _chainId_=1337,
        _verifyingContract_=lixir_vault.address,

        owner=local.address,
        spender=vault_gauge.address,
        value=10**18,
        nonce=0,
        deadline=deadline
    )

    signed = local.sign_message(message)

    vault_gauge.deposit(10**18, local, deadline, signed.signature, {"from": local})
    assert 1 == 0

