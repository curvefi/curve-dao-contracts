# curve-dao-contracts/scripts

Deployment scripts for the Curve DAO.

## Dependencies

* [Brownie](https://github.com/eth-brownie/brownie)
* [Aragon CLI](https://github.com/aragon/aragon-cli)
* [Ganache](https://github.com/trufflesuite/ganache-cli)

## Process Overview

### 1. Initial Setup

[`deployment_config.py`](deployment_config.py) holds configurable / sensitive values related to the deployment. Before starting, you must set the following variables:

* Modify the `get_live_admin` function to return the primary admin [`Account`](https://eth-brownie.readthedocs.io/en/stable/api-network.html#brownie.network.account.Account) object and four funding admin accounts. See the Brownie [account management](https://eth-brownie.readthedocs.io/en/stable/account-management.html) documentation for information on how to unlock local accounts.
* Set vesting information in `STANDARD_ESCROWS` and `FACTORY_ESCROWS`. The structure  of each variable is outlined in the comments.
* Confirm that `LP_VESTING_JSON` points to the JSON which defines the [percentages each historic LP will receive](https://github.com/curvefi/early-user-distribution/blob/master/output-with-bpt.json).

### 2. Deploying the Curve DAO

1. If you haven't already, install [Brownie](https://github.com/eth-brownie/brownie):

    ```bash
    pip install eth-brownie
    ```

2. Verify [`deploy_dao`](deploy_dao.py) by testing in on a forked mainnet:

    ```bash
    brownie run deploy_dao development --network mainnet-fork
    ```

3. Run the [`deploy_dao`](deploy_dao.py) script:

    ```bash
    brownie run deploy_dao live --network mainnet
    ```

    This deploys and links all of the core Curve DAO contracts. A JSON is generated containing the address of each deployed contract. **DO NOT MOVE OR DELETE THIS FILE**. It is required in later deployment stages.

### 3. Deploying the Aragon DAO

1. If you haven't already, install the [Aragon CLI](https://github.com/aragon/aragon-cli):

    ```bash
    npm install --global @aragon/cli
    ```

... TODO ...

Once the DAO is successfully deployed, modify [`deployment_config`](deployment_config.py) so that `ARAGON_AGENT` points to the [Aragon Ownership Agent](https://github.com/aragon/aragon-apps/blob/master/apps/agent/contracts/Agent.sol) deployment.

### 4. Transferring Ownership of Curve DAO to Aragon

1. Verify [`transfer_dao_ownership`](transfer_dao_ownership) by testing it on a forked mainnet:

    ```
    brownie run transfer_dao_ownership development --network mainnet-fork
    ```

2. Run the [`transfer_dao_ownership`](transfer_dao_ownership) script:

    If you haven't yet, modify [`deployment_config`](deployment_config.py) so that `ARAGON_AGENT` points to the [Aragon Ownership Agent](https://github.com/aragon/aragon-apps/blob/master/apps/agent/contracts/Agent.sol) deployment address. Then:

    ```bash
    brownie run transfer_dao_ownership live --network mainnet
    ```

    This transfers the ownership of [`GaugeController`](../contracts/GaugeController.vy), [`PoolProxy`](../contracts/PoolProxy.vy), [`VotingEscrow`](../contracts/VotingEscrow.vy) and [`ERC20CRV`](../contracts/ERC20CRV.vy) from the main admin account to the [Aragon Ownership Agent](https://github.com/aragon/aragon-apps/blob/master/apps/agent/contracts/Agent.sol).

### 5. Distributing Vested Tokens

Vesting distribution is split between historic liquidity providers and other accounts (shareholders, team, etc).

1. Configure [`deployment_config`](deployment_config.py) for this stage:

    * Set the funding admins within the `get_live_admin` function. Funding admins are temporary admin accounts that may only be used to create new vestings. They are used to distribute the workload and complete this job  more quickly - the script makes over 100 transactions!
    * Add info about vested accounts to `STANDARD_ESCROWS` and `FACTORY_ESCROWS`. The structure is outlined within the comments in the config file.

2. Verify [`vest_lp_tokens`](vest_lp_tokens.py) by testing it locally:

    ```bash
    brownie run vest_lp_tokens development
    ```

3. Run the [`vest_lp_tokens`](vest_lp_tokens.py) script:

    Confirm that the admin and funding accounts have sufficient ether to pay for the required gas costs. Then:

    ```bash
    brownie run vest_lp_tokens live --network mainnet
    ```

    This script generates a JSON logging file in case it fails during execution, so you know exactly which transactions were completed.

4. Verify [`vest_other_tokens`](vest_other_tokens.py) by testing it locally:

    ```bash
    brownie run vest_other_tokens development
    ```

5. Run the [`vest_other_tokens`](vest_other_tokens.py) script:

    ```bash
    brownie run vest_other_tokens live --network mainnet
    ```
6. Transfer reserve vesting escrow admin to Aragon Ownership Agent
