import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_real_pool(rpc, accounts, CurvePool, ERC20LP, ERC20, PoolProxy):
    # Test using a real pool which, however, doesn't have all possible methods
    ownership_admin, parameter_admin, emergency_admin = accounts[:3]
    non_admin = accounts[3]
    burner = accounts[4]

    coin_a = ERC20.deploy("Coin A", "USDA", 18, {'from': ownership_admin})
    coin_b = ERC20.deploy("Coin B", "USDB", 18, {'from': ownership_admin})

    lp_token = ERC20LP.deploy("Some pool", "cPool", 18, 0, {'from': ownership_admin})
    pool = CurvePool.deploy([coin_a, coin_b], lp_token, 100, 4 * 10 ** 6, {'from': ownership_admin})
    lp_token.set_minter(pool, {'from': ownership_admin})

    pool_proxy = PoolProxy.deploy({'from': ownership_admin})

    pool.commit_transfer_ownership(pool_proxy, {'from': ownership_admin})
    pool.apply_transfer_ownership({'from': ownership_admin})

    with brownie.reverts():
        pool_proxy.set_admins(ownership_admin, parameter_admin, emergency_admin, {'from': non_admin})
    pool_proxy.set_admins(ownership_admin, parameter_admin, emergency_admin, {'from': ownership_admin})

    with brownie.reverts():
        pool_proxy.set_burner(coin_a, burner, {'from': non_admin})
    pool_proxy.set_burner(coin_a, burner, {'from': ownership_admin})
    pool_proxy.set_burner(coin_b, burner, {'from': ownership_admin})
    pool_proxy.set_burner(ZERO_ADDRESS, burner, {'from': ownership_admin})

    pool_proxy.withdraw_admin_fees(pool, {'from': non_admin})

    with brownie.reverts('dev: should implement burn()'):
        pool_proxy.burn(burner, {'from': non_admin})
    with brownie.reverts('dev: should implement burn_coin()'):
        pool_proxy.burn_coin(coin_a, {'from': non_admin})
    with brownie.reverts('dev: should implement burn_eth()'):
        pool_proxy.burn_eth({'from': non_admin, 'value': 1})

    with brownie.reverts('Access denied'):
        pool_proxy.kill_me(pool, {'from': ownership_admin})
    pool_proxy.kill_me(pool, {'from': emergency_admin})
    with brownie.reverts('Access denied'):
        pool_proxy.unkill_me(pool, {'from': ownership_admin})
    pool_proxy.unkill_me(pool, {'from': emergency_admin})

    with brownie.reverts('Access denied'):
        pool_proxy.commit_transfer_ownership(pool, burner, {'from': non_admin})
    pool_proxy.commit_transfer_ownership(pool, burner, {'from': ownership_admin})
    with brownie.reverts('Access denied'):
        pool_proxy.revert_transfer_ownership(pool, {'from': non_admin})
    pool_proxy.revert_transfer_ownership(pool, {'from': ownership_admin})
    # Actually transfer ownership
    pool_proxy.commit_transfer_ownership(pool, burner, {'from': ownership_admin})
    pool_proxy.apply_transfer_ownership(pool, {'from': ownership_admin})
    # Transfer ownership back
    pool.commit_transfer_ownership(pool_proxy, {'from': burner})
    pool.apply_transfer_ownership({'from': burner})

    with brownie.reverts('Access denied'):
        pool_proxy.commit_new_parameters(pool, 1000, 0, 0, {'from': non_admin})
    with brownie.reverts('dev: if implemented by the pool'):
        pool_proxy.commit_new_parameters(pool, 1000, 0, 0, {'from': parameter_admin})
    with brownie.reverts('dev: if implemented by the pool'):
        pool_proxy.apply_new_parameters(pool, {'from': non_admin})
    with brownie.reverts('Access denied'):
        pool_proxy.revert_new_parameters(pool, {'from': non_admin})
    pool_proxy.revert_new_parameters(pool, {'from': parameter_admin})

    with brownie.reverts('Access denied'):
        pool_proxy.commit_new_fee(pool, 0, 0, {'from': non_admin})
    pool_proxy.commit_new_fee(pool, 0, 0, {'from': parameter_admin})
    pool_proxy.apply_new_fee(pool, {'from': non_admin})
    pool_proxy.commit_new_fee(pool, 1, 1, {'from': parameter_admin})
    with brownie.reverts('Access denied'):
        pool_proxy.revert_new_parameters(pool, {'from': non_admin})
    pool_proxy.revert_new_parameters(pool, {'from': parameter_admin})

    with brownie.reverts('Access denied'):
        pool_proxy.ramp_A(pool, 1000, rpc.time() + 86400 * 2, {'from': non_admin})
    pool_proxy.ramp_A(pool, 1000, rpc.time() + 86400 * 2, {'from': parameter_admin})
    with brownie.reverts('Access denied'):
        pool_proxy.stop_ramp_A(pool, {'from': non_admin})
    pool_proxy.stop_ramp_A(pool, {'from': parameter_admin})
    with brownie.reverts('Access denied'):
        pool_proxy.set_aave_referral(pool, 42, {'from': non_admin})
    with brownie.reverts('dev: if implemented by the pool'):
        pool_proxy.set_aave_referral(pool, 42, {'from': ownership_admin})

    with brownie.reverts('Access denied'):
        pool_proxy.donate_admin_fees(pool, {'from': non_admin})
    with brownie.reverts('dev: if implemented by the pool'):
        pool_proxy.donate_admin_fees(pool, {'from': ownership_admin})
