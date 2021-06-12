# curve-dao-contracts/contracts/gauges/wrappers

Wrappers are used to tokenize deposits in first-gen gauges.

## Contracts

* [`LiquidityGaugeRewardWrapper`](LiquidityGaugeRewardWrapper.vy): ERC20 wrapper for depositing into[`LiquidityGaugeReward`](LiquidityGaugeReward.vy)
* [`LiquidityGaugeWrapper`](LiquidityGaugeWrapper.vy): ERC20 wrapper for depositing into [`LiquidityGauge`](LiquidityGauge.vy)
* [`LiquidityGaugeWrapperUnit`](LiquidityGaugeWrapper.vy): Tokenizes gauge deposits to allow claiming of CRV when deposited as a collateral within the [unit.xyz](https://unit.xyz/) vault.
