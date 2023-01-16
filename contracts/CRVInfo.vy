# @version 0.3.7
"""
@author fiddy
@notice Calculates the circulating supply of Curve DAO token.
@dev The returned circulating supply is an estimate. There might be
     contracts that are not yet accounted for. Should you find one,
     please contact the core dev team.
"""


from vyper.interfaces import ERC20

admin: public(address)
CRV: public(constant(address)) = 0xD533a949740bb3306d119CC777fa900bA034cd52

contracts: public(address[100000])
num_contracts: public(uint256)
LEN_CACHED_CONTRACTS: constant(uint256) = 18
cached_contracts: public(constant(address[LEN_CACHED_CONTRACTS])) = [
    0x41Df5d28C7e801c4df0aB33421E2ed6ce52D2567,  # new employees
    0x2b6509Ca3D0FB2CD1c00F354F119aa139f118bb3,  # vesting
    0xe3997288987E6297Ad550A69B31439504F513267,  # community fund
    0xd061D61a4d941c39E5453435B6345Dc261C2fcE0,  # token minter
    0xd2D43555134dC575BF7279F4bA18809645dB0F1D,  # founder
    0x2A7d59E327759acd5d11A8fb652Bf4072d28AC04,  # investors
    0xa445521569E93D8a87820E593bC9C51C0123da08,  # vesting
    0xD533a949740bb3306d119CC777fa900bA034cd52,  # crv token
    0xf22995a3EA2C83F6764c711115B23A88411CAfdd,  # vesting
    0x575CCD8e2D300e2377B43478339E364000318E2c,  # LPs
    0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2,  # veCRV
    0xf7dBC322d72C1788a1E37eEE738e2eA9C7Fa875e,  # vesting
    0x679FCB9b33Fc4AE10Ff4f96caeF49c1ae3F8fA67,  # employees
    0x81930D767a75269dC0E9b83938884E342c1Fa5F6,
    0x629347824016530Fcd9a1990a30658ed9a04C834,
    0x967E923269475d1Af5718581Ab10bBC6a6154861,
    0xf049ae8D0dDccDD63d479e38aC3C51C4EE64fC2C,
    0x730E9aF9B71D5F41a1EA211347B888024A76612A,
]


@external
def __init__():
    self.admin = msg.sender
    self.num_contracts = 18


@external
def add_contract(_contract: address):
    """
    @notice Adds a contract to the list of contracts to 
            check for CRV balances
    @param _contract Address of the contract to cache
    """
    assert msg.sender == self.admin
    self._add_contract(_contract)


@external
@view
def circulating_supply() -> uint256:
    """
    @notice Returns the circulating supply of CRV
    """
    crv_total_supply: uint256 = ERC20(CRV).totalSupply()
    not_circulating: uint256 = self._get_crv_balances_of_cached_contracts()
    return crv_total_supply - not_circulating


@external
def set_admin(_new_admin: address):
    """
    @notice Set admin. Only callable by current admin.
    @dev We can do lazy admin transfer since this is not a critical contract
    @param _new_admin The new admin address
    """
    assert msg.sender == self.admin
    self.admin = _new_admin


@internal
def _add_contract(_contract: address):
    assert _contract not in self.contracts
    self.contracts[self.num_contracts] = _contract
    self.num_contracts += 1


@internal
@view
def _get_crv_balances_of_cached_contracts() -> uint256:
    
    balances: uint256 = 0
    for i in range(LEN_CACHED_CONTRACTS):
        balances += ERC20(CRV).balanceOf(cached_contracts[i])

    for i in range(10000):
        if self.contracts[i] == empty(address):
            break
        balances += ERC20(CRV).balanceOf(self.contracts[i])

    return balances
