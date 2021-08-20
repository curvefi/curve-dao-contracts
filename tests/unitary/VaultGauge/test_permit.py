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

def test_permit(accounts, lixir_vault, vault_gauge, web3, chain):
    local = accounts.add('8fa2fdfb89003176a16b707fc860d0881da0d1d8248af210df12d37860996fb2')

    message = Permit(
        _name_=web3.keccak(text=lixir_vault.name()),
        _version_=web3.keccak(text='1'),
        _chainId_=1337,
        _verifyingContract_=lixir_vault.address,

        owner=local.address,
        spender=vault_gauge.address,
        value=100,
        nonce=0,
        deadline=chain.time() + 8640
    )

    signed = local.sign_message(message)
    print(type(signed))
    print(signed.messageHash.hex())

    # without name etc.
    # 0x2e6260ed2c9eabd55d3efa8f3603c1598b3a1e698ccb7dd12e336cf13bdbdd4a
    # with name etc.
    # 0x6035834b64d4b8b6d85a7496760644218f3a992df9c7f62bb1cbdd874c7d75d5
    
    # domain_separator = web3.keccak(
    #     encode_abi(
    #         ['bytes32','bytes32','bytes32','uint256','address'],
    #         [
                # web3.keccak(text='EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)'),
                # web3.keccak(text=lixir_vault.name()),
                # web3.keccak(text='1'),
                # 1337,
                # lixir_vault.address
    #         ]
    #     )
    # )

    # struct_hash = web3.keccak(encode_abi_packed(
    #     ['bytes32', 'address', 'address', 'uint256', 'uint256', 'uint256'],
    #     [
    #         web3.keccak(text='Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)'),
    #         accounts[-1].address,
    #         lixir_vault.address,
    #         100, # value
    #         0, # nonce
    #         chain.time() + 86400 * 7 # deadline
    #     ]
    # ))

    # hash_typed_data_v4 = web3.keccak(encode_abi(
    #     ['bytes2', 'bytes32', 'bytes32'],
    #     [b'\x19\x01', domain_separator, struct_hash]
    # ))


    # signed_message = w3.eth.account.sign_message(hash_typed_data_v4, private_key=private_key)

    # print(signed_message)

    assert 1 == 0

