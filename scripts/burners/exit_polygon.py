"""Gracefully exit from Matic ... now in Python.

Script for withdrawing an ERC20 asset from Matic Mainnet back to Ethereum.
This is a two part script, the first portion requires you to burn an ERC20 asset
on the Matic Network, and then after the burn is checkpointed on Ethereum mainnet,
collect the ERC20 asset.

Steps for successful withdrawl:

1. Add Matic ERC20 variable data below
   - MATIC_ERC20_ASSET_ADDR
   - BURN_AMOUNT
2. Call script as follows: `brownie run exit burn_asset_on_matic`
   - Do this in fork mode first ofcourse
3. Add the Burn TX ID below
   - MATIC_BURN_TX_ID
4. Wait a while up to 30 mins
5. Call check inclusion function to see if the burn tx has been checkpointed.
   `brownie run exit is_burn_checkpointed`
6. Once the burn tx has been checkpointed call the exit function
   `brownie run exit exit`
   - Do this in fork mode first ofcourse

To test run: brownie run exit tester --network mainnet
"""
import math
from datetime import datetime
from functools import wraps
from typing import List, Tuple

import rlp
from brownie import Contract, RootForwarder, accounts, chain, network, web3
from brownie.project import get_loaded_projects
from eth_utils import keccak
from hexbytes import HexBytes
from tqdm import tqdm, trange
from trie import HexaryTrie
from web3.types import BlockData, TxReceipt

# Hard coded values for permanent proxy addresses
ADDRS = {
    "mainnet": {
        "RootChainProxy": "0x86E4Dc95c7FBdBf52e33D563BbDB00823894C287",
        "RootChainManagerProxy": "0xA0c68C638235ee32657e8f720a23ceC1bFc77C77",
    },
    "goerli": {
        "RootChainProxy": "0x2890bA17EfE978480615e330ecB65333b880928e",
        "RootChainManagerProxy": "0xBbD7cBFA79faee899Eaf900F13C9065bF03B1A74",
    },
}


PreparedLogs = List[Tuple[bytes, List[bytes], bytes]]
PreparedReceipt = Tuple[bytes, int, bytes, PreparedLogs]

ADDRS["mainnet-fork"] = ADDRS["mainnet"]

# MUST SET VARIABLES BEFORE BURNING ON MATIC
MSG_SENDER = accounts.add()
MATIC_ERC20_ASSET_ADDR = ""
BURN_AMOUNT = 0

# BURN TX HASH
MATIC_BURN_TX_ID = ""


def keccak256(value):
    """Thin wrapper around keccak function."""
    return HexBytes(keccak(value))


def burn_asset_on_matic(asset=MATIC_ERC20_ASSET_ADDR, amount=BURN_AMOUNT, sender=MSG_SENDER):
    """Burn an ERC20 asset on Matic Network"""
    abi = get_loaded_projects()[0].interface.ChildERC20.abi
    asset = Contract.from_abi("ChildERC20", asset, abi)

    tx = asset.withdraw(amount, {"from": sender})
    print("Burn transaction has been sent.")
    print(f"Visit https://explorer-mainnet.maticvigil.com/tx/{tx.txid} for confirmation")


def hot_swap_network(environment_name):
    """Decorator for hot swapping the network connection.

    There is probably a nicer way to do this but I'm lazy and this works.
    This basically hot swaps to the network we want and then back to the
    original network, useful for helper functions.

    Since we are swapping between Ethereum and Matic in this script
    it's neccessary to terminate the RPC and reconnect since Matic
    uses POA ... that sounds about right I really don't know but it works :)

    Args:
        environment_name: A valid environment name found in `brownie networks list`
            e.g. 'ethereum', 'polygon'
    """

    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            initial_network_id = network.show_active()
            is_mainnet = "main" in initial_network_id

            if environment_name == "ethereum":
                swap_network_id = "mainnet" if is_mainnet else "goerli"
            elif environment_name == "polygon":
                swap_network_id = "polygon-main" if is_mainnet else "polygon-testnet"

            if initial_network_id == swap_network_id:
                return func(*args, **kwargs)

            network.disconnect()
            network.connect(swap_network_id)

            result = func(*args, **kwargs)

            network.disconnect()
            network.connect(initial_network_id)

            return result

        return wrapper

    return inner


class MerkleTree:
    """This is my poor but successful lvl 2 copy paste of a merkle tree."""

    def __init__(self, leaves: bytes):
        """Initialize and recursively build the Merkle tree.

        This is only used for building the block proof.

        Args:
            leaves: Serialized blocks
        """
        assert len(leaves) >= 1, "Atleast 1 leaf is needed"
        tree_depth = math.ceil(math.log(len(leaves), 2))
        assert tree_depth <= 20, "Depth must be 20 layers or less"

        self.leaves = leaves + [HexBytes(0) * 32] * (2 ** tree_depth - len(leaves))
        self.layers = [self.leaves]
        self.create_hashes(self.leaves)

    @property
    def root(self) -> bytes:
        """Get the tree root."""
        return self.layers[-1][0]

    def create_hashes(self, nodes: List[bytes]) -> None:
        """Recursively build the layers of the tree."""
        if len(nodes) == 1:
            return

        tree_level = []
        for i in range(0, len(nodes), 2):
            left, right = nodes[i : i + 2]
            new_node = keccak256(left + right)
            tree_level.append(new_node)

        if len(nodes) % 2 == 1:
            tree_level.append(nodes[-1])

        self.layers.append(tree_level)
        self.create_hashes(tree_level)

    def get_proof(self, leaf: bytes) -> List[bytes]:
        """Generate a proof for a leaf."""
        index = self.leaves.index(leaf)

        proof = []
        sibling_index = None
        for i in trange(len(self.layers) - 1, desc="Building merkle proof"):
            if index % 2 == 0:
                sibling_index = index + 1
            else:
                sibling_index = index - 1
            index = index // 2
            sibling_node = self.layers[i][sibling_index]
            proof.append(sibling_node)

        return proof


@hot_swap_network("polygon")
def fetch_burn_tx_data(burn_tx_id: str = MATIC_BURN_TX_ID):
    """Fetch burn tx data."""
    tx = web3.eth.get_transaction(burn_tx_id)
    tx_receipt = web3.eth.get_transaction_receipt(burn_tx_id)
    tx_block = chain[tx["blockNumber"]]

    return tx, tx_receipt, tx_block


@hot_swap_network("ethereum")
def is_burn_checkpointed(burn_tx_id: str = MATIC_BURN_TX_ID, silent: bool = False) -> bool:
    """Check a burn tx has been checkpointed on Ethereum mainnet."""
    _, _, burn_tx_block = fetch_burn_tx_data(burn_tx_id)
    root_chain_proxy_addr = ADDRS[network.show_active()]["RootChainProxy"]
    abi = get_loaded_projects()[0].interface.RootChain.abi
    root_chain = Contract.from_abi("RootChain", root_chain_proxy_addr, abi)

    is_checkpointed = root_chain.getLastChildBlock() >= burn_tx_block["number"]
    if not silent:
        print(f"Has Burn TX been Checkpointed? {is_checkpointed}")
    return is_checkpointed


@hot_swap_network("ethereum")
def fetch_block_inclusion_data(child_block_number: int) -> dict:
    """Fetch burn tx checkpoint block inclusion data.

    Args:
        child_block_number: The block number of the burn tx was included in on
            the matic network
    """
    CHECKPOINT_ID_INTERVAL = 10000

    root_chain_proxy_addr = ADDRS[network.show_active()]["RootChainProxy"]
    abi = get_loaded_projects()[0].interface.RootChain.abi
    root_chain = Contract.from_abi("RootChain", root_chain_proxy_addr, abi)

    start = 1
    end = root_chain.currentHeaderBlock() // CHECKPOINT_ID_INTERVAL

    header_block_number = None
    while start <= end:
        if start == end:
            header_block_number = start

        middle = (start + end) // 2
        header_block = root_chain.headerBlocks(middle * CHECKPOINT_ID_INTERVAL)
        header_start = header_block["start"]
        header_end = header_block["end"]

        if header_start <= child_block_number <= header_end:
            header_block_number = middle
            break
        elif header_start > child_block_number:
            # child block was checkpointed after
            end = middle - 1
        elif header_end < child_block_number:
            # child block was checkpointed before
            start = middle + 1

    return header_start, header_end, header_block_number * CHECKPOINT_ID_INTERVAL


def prepare_receipt(receipt: TxReceipt) -> PreparedReceipt:
    """Prepare a transaction receipt for serialization"""
    receipt_root = HexBytes(receipt.get("root", b""))
    receipt_status = receipt.get("status", 1)

    receipt_root_or_status = receipt_root if len(receipt_root) > 0 else receipt_status
    receipt_cumulative_gas = receipt["cumulativeGasUsed"]
    receipt_logs_bloom = HexBytes(receipt["logsBloom"])
    receipt_logs = [
        (
            HexBytes(log["address"]),
            list(map(HexBytes, log["topics"])),
            HexBytes(log["data"]),
        )
        for log in receipt["logs"]
    ]

    return (
        receipt_root_or_status,
        receipt_cumulative_gas,
        receipt_logs_bloom,
        receipt_logs,
    )


def serialize_receipt(receipt: TxReceipt) -> bytes:
    """Serialize a receipt.

    This also handles EIP-2718 typed transactions.
    """
    prepared_receipt = prepare_receipt(receipt)
    encoded_receipt = rlp.encode(prepared_receipt)

    receipt_type = HexBytes(receipt.get("type", 0))
    if receipt_type == HexBytes(0):
        return encoded_receipt

    buffer = HexBytes(receipt_type) + encoded_receipt
    return rlp.encode(buffer)


def serialize_block(block: dict) -> bytes:
    """Serialize a block."""
    block_number = block["number"].to_bytes(32, "big")
    timestamp = block["timestamp"].to_bytes(32, "big")
    txs_root = HexBytes(block["transactionsRoot"])
    receipts_root = HexBytes(block["receiptsRoot"])
    return keccak256(block_number + timestamp + txs_root + receipts_root)


@hot_swap_network("polygon")
def build_block_proof(block_start: int, block_end: int, burn_tx_block_number: int) -> List[bytes]:
    """Build a merkle proof for the burn tx block."""

    checkpoint_blocks = (
        chain[block_number]
        for block_number in trange(
            block_start, block_end + 1, desc="Serializing blocks", unit="block"
        )
    )
    serialized_blocks = list(map(serialize_block, checkpoint_blocks))

    burn_tx_serialized_block = serialized_blocks[burn_tx_block_number - block_start]
    merkle_tree = MerkleTree(serialized_blocks)

    return merkle_tree.get_proof(burn_tx_serialized_block)


@hot_swap_network("polygon")
def build_receipt_proof(burn_tx_receipt: TxReceipt, burn_tx_block: BlockData) -> List[bytes]:
    """Build the burn_tx_receipt proof."""
    state_sync_tx_hash = keccak256(
        b"matic-bor-receipt-" + burn_tx_block["number"].to_bytes(8, "big") + burn_tx_block["hash"]
    )
    receipts_trie = HexaryTrie({})
    receipts = (
        web3.eth.get_transaction_receipt(tx)
        for tx in tqdm(burn_tx_block["transactions"], desc="Building receipts trie", unit="receipt")
        if tx != state_sync_tx_hash
    )
    for tx_receipt in receipts:
        path = rlp.encode(tx_receipt["transactionIndex"])
        receipts_trie[path] = serialize_receipt(tx_receipt)

    key = rlp.encode(burn_tx_receipt["transactionIndex"])
    print("Building merkle proof")
    proof = receipts_trie.get_proof(key)

    assert (
        receipts_trie.root_hash == burn_tx_block["receiptsRoot"]
    ), "Receipts trie root is incorrect"

    return key, proof


def find_log_index(burn_tx_receipt: TxReceipt) -> int:
    """Retrieve the index of the burn event log."""
    ERC20_TRANSFER_EVENT_SIG = keccak256(b"Transfer(address,address,uint256)")
    for idx, log in enumerate(burn_tx_receipt["logs"]):
        topics = log["topics"]
        if topics[0] == ERC20_TRANSFER_EVENT_SIG and topics[2] == HexBytes(0) * 32:
            return idx

    # this should not be reached
    raise Exception("Transfer Log Event Not Found in Burn Tx Receipt")


def encode_payload(
    header_block_number: int,
    block_proof: List[bytes],
    block_number: int,
    timestamp: int,
    transactions_root: bytes,
    receipts_root: bytes,
    burn_tx_receipt: TxReceipt,
    receipt_proof: List[bytes],
    path: bytes,
    log_index: int,
) -> bytes:
    """RLP encode the data required to form the calldata for exiting."""
    payload = [
        header_block_number,
        b"".join(block_proof),
        block_number,
        timestamp,
        transactions_root,
        receipts_root,
        serialize_receipt(burn_tx_receipt),
        rlp.encode(receipt_proof),
        HexBytes(0) + path,
        log_index,
    ]
    return rlp.encode(payload)


def build_calldata(burn_tx_id: str = MATIC_BURN_TX_ID) -> bytes:
    """Generate the calldata required for withdrawing ERC20 asset on Ethereum."""
    assert is_burn_checkpointed(burn_tx_id)

    burn_tx, burn_tx_receipt, burn_tx_block = fetch_burn_tx_data(burn_tx_id)
    log_index = find_log_index(burn_tx_receipt)
    start, end, header_block_number = fetch_block_inclusion_data(burn_tx_block["number"])
    block_proof = build_block_proof(start, end, burn_tx_block["number"])
    path, receipt_proof = build_receipt_proof(burn_tx_receipt, burn_tx_block)

    calldata = encode_payload(
        header_block_number,
        block_proof,
        burn_tx_block["number"],
        burn_tx_block["timestamp"],
        burn_tx_block["transactionsRoot"],
        burn_tx_block["receiptsRoot"],
        burn_tx_receipt,
        receipt_proof,
        path,
        log_index,
    )
    return calldata


def withdraw_asset_on_ethereum(burn_tx_id: str = MATIC_BURN_TX_ID, sender=MSG_SENDER):
    print("Building Calldata")
    calldata = build_calldata(burn_tx_id)
    fp = f"withdraw-calldata-{datetime.now().isoformat()}.txt"
    with open(fp, "w") as f:
        f.write(calldata.hex())

    root_chain_mgr_proxy_addr = ADDRS[network.show_active()]["RootChainManagerProxy"]
    abi = get_loaded_projects()[0].interface.RootChainManager.abi
    root_chain_mgr = Contract.from_abi("RootChainManager", root_chain_mgr_proxy_addr, abi)

    print("Calling Exit Function on Root Chain Manager")
    root_chain_mgr.exit(calldata, {"from": sender, "priority_fee": "2 gwei"})

    # transfer USDC out of the root receiver
    usdc = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    root_receiver = RootForwarder.at("0x28542E4AF3De534ca36dAF342febdA541c937C5a")
    root_receiver.transfer(usdc, {"from": sender, "priority_fee": "2 gwei"})


def main():

    route = input(
        """
Choose an option:
(1) Burn an asset on Matic
(2) Withdraw an asset on Ethereum
(3) Check burn tx checkpoint
Choice: """
    )
    try:
        route = int(route)
    except ValueError:
        exit()

    if route == 1:
        asset = input("Input token to burn on matic: ")
        amount = int(input("Input amount of token to burn: "))
        sender = (
            accounts.load(input("Account name: "))
            if input("Do you want to load an account? [y/N] ") == "y"
            else MSG_SENDER
        )
        burn_asset_on_matic(asset, amount, sender)
    elif route == 2:
        burn_tx_hash = input("Input matic burn tx hash: ")
        sender = (
            accounts.load(input("Account name: "))
            if input("Do you want to load an account? [y/N] ") == "y"
            else MSG_SENDER
        )
        withdraw_asset_on_ethereum(burn_tx_hash, sender)
    elif route == 3:
        burn_tx_hash = input("Enter burn tx hash: ")
        bar_fmt = "Blocks Mined: {n} blocks - Time Elapsed: {elapsed}"
        for block in tqdm(chain.new_blocks(1), bar_format=bar_fmt):
            if is_burn_checkpointed(burn_tx_hash, True):
                print(f"Tx {burn_tx_hash} has been checkpointed in block {block['number']}")
                break


def test_calldata(burn_tx: str, exit_tx: str):
    print(f"Testing Burn TX: {burn_tx}")

    root_chain_mgr_proxy_addr = ADDRS[network.show_active()]["RootChainManagerProxy"]
    abi = get_loaded_projects()[0].interface.RootChainManager.abi
    root_chain_mgr = Contract.from_abi("RootChainManager", root_chain_mgr_proxy_addr, abi)

    calldata = HexBytes(root_chain_mgr.exit.encode_input(build_calldata(burn_tx)))
    input_data = HexBytes(web3.eth.get_transaction(exit_tx)["input"])

    assert calldata == input_data
    print("Test passed")


def tester():
    # (burn_tx, exit_tx)
    test_txs = [
        (
            "0x4486e398e0f2ca4d00bec85edbb9aff94e7085fa2b5ef18319989d9d8e37152f",
            "0x6fe5d2638e7bdbf598c215c6d20b6bf2cad58479460091c0f2330506c14762bf",
        ),
        (
            "0xbcaafea9bed5c31dc2472a015afca6463a5de14730a3a6ab4501475c0594cfc4",
            "0x1afcfe324fcfa0fbf54182524e74fc57ff8ddff58367529af519adbaccc13f7a",
        ),
        (
            "0x7d17b4cfbab16739bf00cead6ffec306f7420ec5c91de4ac1d485b7de9efaf49",
            "0xfed6fc9558d45b0672fe9ff23d341d028d99f71a318feabf925f0d1b67eea503",
        ),
    ]
    for burn_tx, exit_tx in test_txs:
        test_calldata(burn_tx, exit_tx)
    print("All works as expected.")
