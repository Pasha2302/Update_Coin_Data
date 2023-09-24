import os
from decimal import Decimal
import toolbox
from web3 import Web3

ADDRESS_V3_v2 = {"V3": "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865", "V2": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"}
disposal_addresses = [
    "0x000000000000000000000000000000000000dead",
    "0x0000000000000000000000000000000000000000",
    "0x0000000000000000000000000000000000000001"
]

current_directory = os.path.dirname(__file__)
name_dir_abis = 'contract_abis'
name_file_abi_router_helper = "contract_abiRouterHelper.json"
file_name_erc20 = "ERC20.json"
path_abi_router_helper = os.path.join(current_directory, name_dir_abis, name_file_abi_router_helper)
path_erc20_contract = os.path.join(current_directory, name_dir_abis, file_name_erc20)

abi_router_helper = toolbox.download_json_data(path_file=path_abi_router_helper)
ERC20 = toolbox.download_json_data(path_file=path_erc20_contract)
contract_address_router_helper = '0xdAecee3C08e953Bd5f89A5Cc90ac560413d709E3'


class RouterHelper:
    router_helper_contract = None

    def __init__(self, w3: Web3 | None = None):
        self.w3 = w3
        self.__erc20_contract = ERC20
        if w3 is None:
            self.__set_w3()

        if RouterHelper.router_helper_contract is None:  # Проверка, создана ли переменная класса
            RouterHelper.router_helper_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(contract_address_router_helper),
                abi=abi_router_helper)

    def __set_w3(self):
        from web3_connector import Web3Conn
        self.w3: Web3 = Web3Conn().get_w3()

    def get_reserves(self, contract_address_main_coin, contract_address_coin):
        error_reserves = False

        for address_key in ADDRESS_V3_v2:
            factory_address = ADDRESS_V3_v2[address_key]
            try:
                result = self.router_helper_contract.functions.getReserves(
                    factory_address,
                    self.w3.to_checksum_address(contract_address_main_coin),
                    self.w3.to_checksum_address(contract_address_coin)).call()
                return result
            except Exception as err:
                # print(f"\n!!! > [29] << Ошибка при вызове функции: getReserves() >>:\n{err}")
                error_reserves = err

        if error_reserves:
            return {
                "error": str(error_reserves),
            }

    def calculate_circulating_supply(self, contract_address_coin, coin_decimals, supply):
        count_utilized_tokens = Decimal(0)

        # print(f"{circulating_supply=}\n{contract_address_coin=}")
        try:
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address_coin), abi=self.__erc20_contract)
        except Exception as error_token_contract:
            # str_error1 = f"\n!!! [get_market_cap]\n{contract_address_coin=}\n{error_token_contract}"
            # print(f"{str_error1}")
            return {
                'error': str(error_token_contract),
                "token_address_b": contract_address_coin,
                "in_func": "< get_market_cap.token_contract >"
            }
        for addresses_d in disposal_addresses:
            try:
                count_utilized_tokens += Decimal(token_contract.functions.balanceOf(
                    Web3.to_checksum_address(addresses_d)).call()) / Decimal(10 ** coin_decimals)
            except Exception as error:
                # str_error2 = f"\n!!! [get_market_cap.balanceOf]\n{contract_address_coin=}\n{error}"
                # print(f"{str_error2}")
                if '403 Client Error' in str(error):
                    return {'error': str(error)}
                pass
        circulating_supply = Decimal(supply) - count_utilized_tokens
        return circulating_supply

    def get_coin_info(
            self, token_address, input_decimals=True, get_symbol=None, get_name=None,
            get_decimals=None, get_total_supply=None, get_full=None, get_circulating_supply=None
    ):
        symbol = name = total_supply = decimals = circulating_supply = None
        if get_full:
            get_symbol = get_name = get_decimals = get_total_supply = True

        try:
            coin_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address), abi=self.__erc20_contract
            )

            if get_symbol:
                symbol = coin_contract.functions.symbol().call()
            if get_name:
                name = coin_contract.functions.name().call()
            if get_decimals or not input_decimals:
                decimals = int(coin_contract.functions.decimals().call())
                input_decimals = decimals
            if get_total_supply:
                # Получение общего предложения токена
                # Decimal(10 ** decimals) - преобразование из wei в ether
                total_supply = Decimal(coin_contract.functions.totalSupply().call()) / Decimal(10 ** input_decimals)

        except Exception as error_info_token:
            return {
                "error": str(error_info_token),
                "token_address_b": token_address,
                "in_func": "< get_token_info >"
            }

        if get_circulating_supply and total_supply:
            circulating_supply = self.calculate_circulating_supply(token_address, input_decimals, total_supply)
            if isinstance(circulating_supply, dict):
                return circulating_supply
        return {
            'symbol': symbol,
            'name': name,
            'supply': total_supply,
            'decimals': decimals,
            'circulating_supply': circulating_supply
        }
