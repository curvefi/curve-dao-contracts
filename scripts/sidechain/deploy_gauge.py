from brownie import (
    ZERO_ADDRESS,
    ChildChainStreamer,
    Contract,
    RewardClaimer,
    RewardsOnlyGauge,
    accounts,
)

CRV = {
    "ftm": "0x1E4F97b9f9F913c46F1632781732927B9019C68b",
    "polygon": "0x172370d5cd63279efa6d502dab29171933a610af",
}

STREAM_DEPLOYER = {
    "ftm": "0x0000c13f1d4a5832120a895d7484660d31fb784f",
    "polygon": "0x0000d7b833bb2b5caa98be580d65a9236d6cc5ea",
}
CONFS = 3


def main(network_name, lp_token):
    deployer = accounts.at("0x7EeAC6CDdbd1D0B8aF061742D41877D7F707289a", True)
    stream_deployer = accounts.at(STREAM_DEPLOYER[network_name], True)
    crv = Contract(CRV[network_name])

    gauge = RewardsOnlyGauge.deploy(deployer, lp_token, {"from": deployer, "required_confs": CONFS})
    claimer = RewardClaimer.deploy(deployer, gauge, {"from": deployer, "required_confs": CONFS})
    streamer = ChildChainStreamer.deploy(
        deployer, claimer, crv, {"from": stream_deployer, "required_confs": CONFS}
    )
    claimer.set_reward_data(0, streamer, crv, {"from": deployer, "required_confs": CONFS})

    gauge.set_rewards(
        claimer,
        f"0x0000000000000000{claimer.get_reward.signature[2:]}" + "00" * 20,
        [crv] + [ZERO_ADDRESS] * 7,
        {"from": deployer, "required_confs": CONFS},
    )
