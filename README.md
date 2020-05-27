Contracts for Curve DAO
=========================

Curve DAO is based on Aragon with few differences from a typical way of doing
things.

Time-weighted voting with VotingEscrow
----------------------------------------
Instead of voting with token number `amount`, in Curve DAO tokens are lockable
in a VotingEscrow for a selectable time `locktime`, where `locktime < MAXTIME`
and `MAXTIME = 4 years`. The voting weight is equal to `amount * locktime / MAXTIME`.
In other words, vote is also time-weighted.

The account which locks the tokens cannot be a smart contract (b/c can be
tradable and tokenized) unless it is one of whitelisted smart contracts.

VotingEscrow tries to resemble Aragon's Minime token. Most importantly, it
returns `balanceOfAt()` and `totalSupplyAt()` where instead of balances voting
weight at a block is returned.

Locks can be created or extended with `deposit()`, and `withdraw()` can remove
tokens from the escrow when the lock is expired.

Inflation schedule. ERC20CRV
---------------------------------
Token ERC20CRV follows a piecewise linear inflation schedule with inflation
dropping by sqrt(2) every year. Only Minter contract can directly mine ERC20CRV
but only within the limits defined by inflation.

Each time the inflation changes, a new mining epoch starts.

System of Gauges. LiquidityGauge and GaugeController
------------------------------------------------------
In Curve, inflation is going towards users who use it. The usage is measured
with Gauges. Currently there is just LiquidityGauge which measures, how much
liquidity does the user provide.

For LiquidityGauge to measure user liquidity over time, the user deposits
his LP tokens into the gauge using `deposit()` and can withdraw using `withdraw()`.

Coin rates which the gauge is getting depends on current inflation rate,
and gauge type weights (which get voted on in Aragon). Each user gets inflation
proportional to his LP tokens locked. We do iterated calculations of inverse
locked supply integral, so it is not required for user to periodically check in.

GaugeController keeps a list of Gauges and their types, with weights of each
gauge and type.

Gauges are per pool (each pool has an individual gauge).

Weight voting for gauges
--------------------------

Instead of simply voting for weight change in Aragon, users can allocate their
vote-locked tokens towards one or other Gauge (pool). That pool will be getting
a fraction of CRV tokens minted proportional to how much vote-locked tokens are
allocated to it. Eeach user with tokens in VotingEscrow can change his/her
preference at any time.
