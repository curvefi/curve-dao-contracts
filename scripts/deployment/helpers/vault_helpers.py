from scripts.helpers.imports import IERC20
from lixir.system import VaultDeployParameters

base_params = {
    "strategy": {
        "type": "simple_gwap",
        "fee": 3000,
        "tick_short_duration": 60,
        "max_tick_diff": 180,
        "main_spread": 1800,
        "range_spread": 900,
    }
}

tokenPairs = [
    (("USD Tether", "USDT"), ("USD Coin", "USDC")),
    (("USD Coin", "USDC"), ("Wrapped Bitcoin", "WBTC")),
    (("renVM Bitcoin", "renBTC"), ("Wrapped Bitcoin", "WBTC")),
]

ethTokenPairs = [
    ("USD Coin", "USDC"),
    ("Wrapped Bitcoin", "WBTC"),
    ("Lixir", "LIX"),
]

tokenSet = set(v for w in tokenPairs for v in w).union(ethTokenPairs)


def config_to_args(config):
    assert config["strategy"]["type"] == "simple_gwap"
    assert len(config["tokens"]) == 2
    return VaultDeployParameters(
        config["name"],
        config["symbol"],
        IERC20(config["tokens"][0]),
        IERC20(config["tokens"][1]),
        config["strategy"]["fee"],
        config["strategy"]["tick_short_duration"],
        config["strategy"]["max_tick_diff"],
        config["strategy"]["main_spread"],
        config["strategy"]["range_spread"],
    )

 