import pytest
from brownie_tokens import MintableForkToken


class _MintableTestToken(MintableForkToken):
    def __init__(self, address):
        super().__init__(address)


@pytest.fixture(scope="session")
def MintableTestToken():
    yield _MintableTestToken


@pytest.fixture(scope="module")
def USDC():
    yield _MintableTestToken("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")


@pytest.fixture(scope="module")
def ThreeCRV():
    yield _MintableTestToken("0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490")


@pytest.fixture(scope="module")
def SUSD():
    yield _MintableTestToken("0x57ab1ec28d129707052df4df418d58a2d46d5f51")


@pytest.fixture(scope="module")
def SBTC():
    yield _MintableTestToken("0xfE18be6b3Bd88A2D2A7f928d00292E7a9963CfC6")


@pytest.fixture(scope="module")
def WETH():
    yield _MintableTestToken("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")


@pytest.fixture(scope="module")
def USDT():
    yield _MintableTestToken("0xdac17f958d2ee523a2206206994597c13d831ec7")


@pytest.fixture(scope="module")
def DAI():
    yield _MintableTestToken("0x6B175474E89094C44Da98b954EedeAC495271d0F")
