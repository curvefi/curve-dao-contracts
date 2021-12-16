import brownie
from eip712.messages import EIP712Message


def test_permit(accounts, bob, chain, gauge_v5):

    alice = accounts.add("0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09")

    class Permit(EIP712Message):
        # EIP-712 Domain Fields
        _name_: "string" = gauge_v5.name()  # noqa: F821
        _version_: "string" = gauge_v5.version()  # noqa: F821
        _chainId_: "uint256" = chain.id  # noqa: F821
        _verifyingContract_: "address" = gauge_v5.address  # noqa: F821

        # EIP-2612 Data Fields
        owner: "address"  # noqa: F821
        spender: "address"  # noqa: F821
        value: "uint256"  # noqa: F821
        nonce: "uint256"  # noqa: F821
        deadline: "uint256" = 2 ** 256 - 1  # noqa: F821

    permit = Permit(owner=alice.address, spender=bob.address, value=2 ** 256 - 1, nonce=0)
    sig = alice.sign_message(permit)

    tx = gauge_v5.permit(alice, bob, 2 ** 256 - 1, 2 ** 256 - 1, sig.v, sig.r, sig.s)

    assert gauge_v5.allowance(alice, bob) == 2 ** 256 - 1
    assert tx.return_value is True
    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [alice.address, bob, 2 ** 256 - 1]
    assert gauge_v5.nonces(alice) == 1


def test_permit_contract(accounts, bob, chain, gauge_v5):

    src = """
@view
@external
def isValidSignature(_hash: bytes32, _sig: Bytes[65]) -> bytes32:
    return 0x1626ba7e00000000000000000000000000000000000000000000000000000000
    """
    mock_contract = brownie.compile_source(src, vyper_version="0.3.1").Vyper.deploy({"from": bob})
    alice = accounts.add("0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09")

    class Permit(EIP712Message):
        # EIP-712 Domain Fields
        _name_: "string" = gauge_v5.name()  # noqa: F821
        _version_: "string" = gauge_v5.version()  # noqa: F821
        _chainId_: "uint256" = chain.id  # noqa: F821
        _verifyingContract_: "address" = gauge_v5.address  # noqa: F821

        # EIP-2612 Data Fields
        owner: "address"  # noqa: F821
        spender: "address"  # noqa: F821
        value: "uint256"  # noqa: F821
        nonce: "uint256"  # noqa: F821
        deadline: "uint256" = 2 ** 256 - 1  # noqa: F821

    permit = Permit(owner=alice.address, spender=bob.address, value=2 ** 256 - 1, nonce=0)
    sig = alice.sign_message(permit)

    tx = gauge_v5.permit(mock_contract, bob, 2 ** 256 - 1, 2 ** 256 - 1, sig.v, sig.r, sig.s)

    # make sure this is hit when owner is a contract
    assert tx.subcalls[0]["function"] == "isValidSignature(bytes32,bytes)"
