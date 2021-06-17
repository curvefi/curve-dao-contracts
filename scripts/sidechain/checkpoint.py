from brownie import Contract, accounts

FTM = [
    "0xb9C05B8EE41FDCbd9956114B3aF15834FDEDCb54",  # 2pool
    "0xfE1A3dD8b169fB5BF0D5dbFe813d956F39fF6310",  # fusdt
]
POLYGON = [
    "0xC48f4653dd6a9509De44c92beb0604BEA3AEe714",  # am3pool
]


def main():
    acct = accounts.load("curve-deploy")
    checkpoint = Contract("0xa549ffd8e439c4ff746659ed80a6c5e55f9cf3cf")
    for addr in FTM + POLYGON:
        checkpoint.checkpoint(addr, {"from": acct})


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
        streamer.notify_reward_amount(token, {"from": acct})
