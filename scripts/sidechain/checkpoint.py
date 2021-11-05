from brownie import Contract, accounts, history

# this script is used for bridging CRV rewards to sidechains
# it should be run once per week, just after the start of the epoch week

FTM = [
    "0xb9C05B8EE41FDCbd9956114B3aF15834FDEDCb54",  # 2pool
    "0xfE1A3dD8b169fB5BF0D5dbFe813d956F39fF6310",  # fusdt
    "0xfDb129ea4b6f557b07BcDCedE54F665b7b6Bc281",  # ren
    "0x260e4fBb13DD91e187AE992c3435D0cf97172316",  # tricrypto
]
POLYGON = [
    "0xC48f4653dd6a9509De44c92beb0604BEA3AEe714",  # am3pool
    "0x060e386eCfBacf42Aa72171Af9EFe17b3993fC4F",  # aTriCrypto
    "0x488E6ef919C2bB9de535C634a80afb0114DA8F62",  # ren
]
XDAI = [
    "0x6C09F6727113543Fd061a721da512B7eFCDD0267",  # x3pool
]

ARBITRUM = [
    "0xFf17560d746F85674FE7629cE986E949602EF948",  # 2pool
    "0x9F86c5142369B1Ffd4223E5A2F2005FC66807894",  # ren
    "0x9044E12fB1732f88ed0c93cfa5E9bB9bD2990cE5",  # tricrypto
]

AVAX = [
    "0xB504b6EB06760019801a91B451d3f7BD9f027fC9",
    "0x75D05190f35567e79012c2F0a02330D3Ed8a1F74",
    "0xa05e565ca0a103fcd999c7a7b8de7bd15d5f6505",
]

HARMONY = [
    "0xf2Cde8c47C20aCbffC598217Ad5FE6DB9E00b163",
]


def main():
    acct = accounts.load("curve-deploy")

    # xdai/polygon bridge takes longer so we do it first
    for addr in POLYGON + XDAI:
        Contract(addr).checkpoint({"from": acct, "priority_fee": "2 gwei"})

    # for abritrum, the L1 transaction must include ETH to pay for the L2 transaction
    for addr in ARBITRUM:
        gauge = Contract(addr)
        value = gauge.get_total_bridge_cost()
        gauge.checkpoint(
            {"from": acct, "priority_fee": "2 gwei", "required_confs": 0, "value": value}
        )

    # for fantom, harmony, avax we must call the gauge through the checkpoint
    # contract in order for the bridge to recognize the transaction
    checkpoint = Contract("0xa549ffd8e439c4ff746659ed80a6c5e55f9cf3cf")
    for addr in FTM + HARMONY + AVAX:
        checkpoint.checkpoint(addr, {"from": acct, "priority_fee": "2 gwei", "required_confs": 0})

    history.wait()


def fantom():
    acct = accounts.load("curve-deploy")
    for addr in FTM:
        streamer = Contract(addr)
        token = streamer.reward_tokens(0)
        streamer.notify_reward_amount(token, {"from": acct})


def polygon():
    acct = accounts.load("curve-deploy")
    for addr in POLYGON:
        streamer = Contract(addr)
        token = streamer.reward_tokens(0)
        streamer.notify_reward_amount(token, {"from": acct, "gas_price": "50 gwei"})


def xdai():
    acct = accounts.load("curve-deploy")
    for addr in XDAI:
        streamer = Contract(addr)
        token = streamer.reward_tokens(0)
        streamer.notify_reward_amount(token, {"from": acct})


def arbitrum():
    acct = accounts.load("curve-deploy")
    for addr in ARBITRUM:
        streamer = Contract(addr)
        token = streamer.reward_tokens(0)
        streamer.notify_reward_amount(token, {"from": acct})


def harmony():
    acct = accounts.load("curve-deploy")
    for addr in HARMONY:
        streamer = Contract(addr)
        token = streamer.reward_tokens(0)
        streamer.notify_reward_amount(token, {"from": acct})


def avax():
    acct = accounts.load("curve-deploy")
    for addr in AVAX:
        streamer = Contract(addr)
        token = streamer.reward_tokens(0)
        streamer.notify_reward_amount(token, {"from": acct})
