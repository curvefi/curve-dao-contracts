# curve-dao-contracts/contracts

All contract sources are within this directory.

## Subdirectories

* [`gauges`](gauges): Contracts used for measuring provided liquidity
* [`testing`](testing): Contracts used exclusively for testing. Not considered to be a core part of this project.

## Contracts

* [`ERC20CRV`](ERC20CRV.vy): Curve DAO Token (CRV), an [ERC20](https://eips.ethereum.org/EIPS/eip-20) with piecewise-linear mining supply
* [`GaugeController`](GaugeController.vy): Controls liquidity gauges and the issuance of CRV through the liquidity gauges
* [`LiquidityGauge`](LiquidityGauge.vy): Measures the amount of liquidity provided by each user
* [`LiquidityGaugeReward`](LiquidityGaugeReward.vy): Measures provided liquidity and stakes using [Synthetix rewards contract](https://github.com/Synthetixio/synthetix/blob/master/contracts/StakingRewards.sol)
* [`Minter`](Minter.vy): Token minting contract used for issuing new CRV
* [`PoolProxy`](PoolProxy.vy): StableSwap pool proxy contract for interactions between the DAO and pool contracts
* [`VestingEscrow`](VestingEscrow.vy): Vests CRV tokens for multiple addresses over multiple vesting periods
* [`VestingEscrowFactory`](VestingEscrowFactory.vy): Factory to store CRV and deploy many simplified vesting contracts
* [`VestingEscrowSimple`](VestingEscrowSimple.vy): Simplified vesting contract that holds CRV for a single address
* [`VotingEscrow`](VotingEscrow.vy): Vesting contract for locking CRV to participate in DAO governance
