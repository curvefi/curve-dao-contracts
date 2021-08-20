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


def test_permit(local, lixir_vault, vault_gauge_lix, web3, chain):
    deadline = chain.time() + 86400
    message = Permit(
        _name_=lixir_vault.name(),
        _version_='1',
        _chainId_=1337,
        _verifyingContract_=lixir_vault.address,

        owner=local.address,
        spender=vault_gauge_lix.address,
        value=10**6,
        nonce=0,
        deadline=deadline
    )

    signed = local.sign_message(message)
    # print(signed.signature)

    print(lixir_vault.balanceOf(local))

    lixir_vault.deposit(10**6, 10**6, 0, 0, local.address, deadline, {"from": local})
    print(lixir_vault.balanceOf(local))

    lixir_vault.approve(vault_gauge_lix, 200000, {"from": local})
    vault_gauge_lix.deposit(200000, local.address) # , deadline, signed.signature)

    assert 1 == 0

