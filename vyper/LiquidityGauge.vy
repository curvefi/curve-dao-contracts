# This gauge can be used for measuring liquidity and insurance

# This is not required at all, but let's define here for commentary purposes
contract LiquidityGauge:
    def measure_of(addr: address) -> uint256: constant
    def measure_total() -> uint256: constant
    def integrate_fraction(addr: address, start: uint256, end: uint256) -> uint256: constant


@public
def __init__():
    pass


@public
@constant
def measure_of(addr: address) -> uint256:
    return 0


@public
@constant
def measure_total() -> uint256:
    return 0


@public
@constant
def integrate_fraction(addr: address, start: uint256, end: uint256) -> uint256:
    return 0
