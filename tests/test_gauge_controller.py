def test_gauge_controller(w3, gauge_controller, liquidity_gauge, three_gauges):
    admin = w3.eth.accounts[0]
    from_admin = {'from': admin}
    type_weights = [5 * 10 ** 17, 2 * 10 ** 18]
    gauge_weights = [2 * 10 ** 18, 10 ** 18, 5 * 10 ** 17]

    # Set up gauges and types
    gauge_controller.functions.add_type().transact(from_admin)  # 0
    gauge_controller.functions.add_type().transact(from_admin)  # 1
    gauge_controller.functions.change_type_weight(0, type_weights[0]).transact(from_admin)

    gauge_controller.functions.add_gauge(three_gauges[0].address, 0).transact(from_admin)
    gauge_controller.functions.add_gauge(three_gauges[1].address, 0, gauge_weights[1]).transact(from_admin)
    gauge_controller.functions.add_gauge(three_gauges[2].address, 1, gauge_weights[2]).transact(from_admin)

    gauge_controller.functions.change_type_weight(1, type_weights[1]).transact(from_admin)

    gauge_controller.functions.change_gauge_weight(three_gauges[0].address, gauge_weights[0]).transact(from_admin)
