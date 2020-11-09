import pytest
import requests

from brownie import Contract
from brownie.convert import to_address

_holders = {}


class _MintableTestToken(Contract):

    def __init__(self, address):
        super().__init__(address)

        # get top token holder addresses
        address = self.address
        if address not in _holders:
            holders = requests.get(
                f"https://api.ethplorer.io/getTopTokenHolders/{address}",
                params={'apiKey': "freekey", 'limit': 50},
            ).json()
            _holders[address] = [to_address(i['address']) for i in holders['holders']]

    def _mint_for_testing(self, target, amount, tx=None):
        if self.address == "0x674C6Ad92Fd080e4004b2312b45f796a192D27a0":
            # USDN
            self.deposit(target, amount, {'from': "0x90f85042533F11b362769ea9beE20334584Dcd7D"})
            return
        if self.address == "0x0E2EC54fC0B509F445631Bf4b91AB8168230C752":
            # LinkUSD
            self.mint(target, amount, {'from': "0x62F31E08e279f3091d9755a09914DF97554eAe0b"})
            return
        if self.address == "0x196f4727526eA7FB1e17b2071B3d8eAA38486988":
            # RSV
            self.changeMaxSupply(2**128, {'from': self.owner()})
            self.mint(target, amount, {'from': self.minter()})
            return

        for address in _holders[self.address].copy():
            if address == self.address:
                # don't claim from the treasury - that could cause wierdness
                continue

            balance = self.balanceOf(address)
            if amount > balance:
                self.transfer(target, balance, {'from': address})
                amount -= balance
            else:
                self.transfer(target, amount, {'from': address})
                return

        raise ValueError(f"Insufficient tokens available to mint {self.name()}")


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
