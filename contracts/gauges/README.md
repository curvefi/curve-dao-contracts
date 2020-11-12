# curve-dao-contracts/contracts/gauges

Contracts used for measuring provided liquidity within Curve pools.

## Contracts

* [`LiquidityGauge`](LiquidityGauge.vy): Measures the amount of liquidity provided by each user
* [`LiquidityGaugeReward`](LiquidityGaugeReward.vy): Measures provided liquidity and stakes using [Synthetix rewards contract](https://github.com/Synthetixio/synthetix/blob/master/contracts/StakingRewards.sol)
* [`LiquidityGaugeRewardWrapper`](LiquidityGaugeRewardWrapper.vy): ERC20 wrapper for depositing into[`LiquidityGaugeReward`](LiquidityGaugeReward.vy)
* [`LiquidityGaugeWrapper`](LiquidityGaugeWrapper.vy): ERC20 wrapper for depositing into [`LiquidityGauge`](LiquidityGauge.vy)
