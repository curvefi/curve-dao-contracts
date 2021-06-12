import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS, Contract


@pytest.fixture(scope="module")
def receiver(UnderlyingBurner, alice, receiver):
    yield UnderlyingBurner.deploy(receiver, receiver, alice, alice, {"from": alice})


@pytest.fixture(scope="module")
def burner(SynthBurner, alice, receiver):
    contract = SynthBurner.deploy(receiver, receiver, alice, alice, {"from": alice})

    contract.add_synths(SYNTHS + [ZERO_ADDRESS] * (10 - len(SYNTHS)), {"from": alice})

    tokens = [i[0] for i in SWAP_FOR]
    targets = [i[1] for i in SWAP_FOR]
    tokens += [ZERO_ADDRESS] * (10 - len(tokens))
    targets += [ZERO_ADDRESS] * (10 - len(targets))
    contract.set_swap_for(tokens, targets, {"from": alice})

    yield contract


SYNTHS = [
    "0x5e74C9036fb86BD7eCdcb084a0673EFc32eA31cb",  # sETH
    "0xD71eCFF9342A5Ced620049e616c5035F1dB98620",  # sEUR
    "0xbBC455cb4F1B9e4bFC4B73970d360c8f032EfEE6",  # sLINK
    "0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6",  # sBTC
]
susd = "0x57ab1ec28d129707052df4df418d58a2d46d5f51"

SWAP_FOR = [
    (ETH_ADDRESS, "0x5e74C9036fb86BD7eCdcb084a0673EFc32eA31cb"),
    ("0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84", ETH_ADDRESS),
    ("0xE95A203B1a91a908F9B9CE46459d101078c2c3cb", ETH_ADDRESS),
    ("0x9559Aaa82d9649C7A7b220E7c461d2E74c9a3593", ETH_ADDRESS),
    ("0xdB25f211AB05b1c97D595516F45794528a807ad8", "0xD71eCFF9342A5Ced620049e616c5035F1dB98620"),
    ("0x514910771AF9Ca656af840dff83E8264EcF986CA", "0xbBC455cb4F1B9e4bFC4B73970d360c8f032EfEE6"),
    ("0xeb4c2781e4eba804ce9a9803c67d0893436bb27d", "0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6"),
    ("0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", "0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6"),
    ("0x8dAEBADE922dF735c38C80C7eBD708Af50815fAa", "0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6"),
    ("0x0316EB71485b0Ab14103307bf65a021042c6d380", "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"),
]


@pytest.mark.parametrize("token,target", SWAP_FOR + [(i, susd) for i in SYNTHS])
@pytest.mark.parametrize("burner_balance", (True, False))
@pytest.mark.parametrize("caller_balance", (True, False))
def test_swap(
    MintableTestToken, SUSD, alice, receiver, burner, token, target, burner_balance, caller_balance
):
    if token == ETH_ADDRESS:
        coin = token
        eth_amount = 10 ** 18 if caller_balance or burner_balance else 0
    else:
        coin = MintableTestToken(token)
        eth_amount = 0
        amount = 10 ** coin.decimals()

        if caller_balance:
            coin._mint_for_testing(alice, amount, {"from": alice})
            coin.approve(burner, 2 ** 256 - 1, {"from": alice})

        if burner_balance:
            coin._mint_for_testing(burner, amount, {"from": alice})

    burner.burn(coin, {"from": alice, "value": eth_amount})

    if burner_balance or caller_balance:
        if token != ETH_ADDRESS:
            assert coin.balanceOf(alice) < 2
            assert coin.balanceOf(burner) < 2
            assert coin.balanceOf(receiver) == 0

        if target == ETH_ADDRESS:
            assert burner.balance() > 0
        elif target == SUSD:
            assert SUSD.balanceOf(alice) == 0
            assert SUSD.balanceOf(burner) == 0
            assert SUSD.balanceOf(receiver) > 0
        else:
            target = Contract(target)
            assert target.balanceOf(alice) == 0
            assert target.balanceOf(burner) > 0
            assert target.balanceOf(receiver) == 0
