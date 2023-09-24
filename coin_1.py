from datetime import datetime
from decimal import Decimal

from web3 import Web3
import mysql.connector
import mysql.connector.cursor

from router_w3 import RouterHelper
from global_variables import GlobalVariables as Gv

ETHER = 10 ** 18


def _get_data_coin_local_db(
        table: str | None = None, where: str | None = None, input_query: str | None = None) -> list[dict] | None:
    where_str = ""
    with mysql.connector.connect(**Gv.db_config_mooner_local) as conn:
        conn: mysql.connector.connection.MySQLConnection
        conn.database = 'coinmooner'
        with conn.cursor(dictionary=True) as cur:
            cur: mysql.connector.cursor.MySQLCursor
            if where:
                where_str = f" WHERE {where}"
            query = f"SELECT * FROM {table}{where_str}"

            try:
                if input_query:
                    query = input_query
                cur.execute(query)
            except mysql.connector.errors.ProgrammingError as error_connector:
                if "Table 'coinmooner.coin' doesn't exist" in str(error_connector):
                    return None
            else:
                res = cur.fetchall()
                if res:
                    return res


class MainCoin:
    coin_id = None
    name = None
    symbol = None
    contract_address = None
    decimals = None
    supply = None
    reserves = None

    @classmethod
    def get_data_for_table_main_coin(cls):
        dict_data_table_main_coin = {
            "mainCoinId": cls.coin_id, "name": cls.name, "symbol": cls.symbol,
            "contractAddress": cls.contract_address, "supply": cls.supply,
            "decimals": cls.decimals}
        return dict_data_table_main_coin

    @classmethod
    def set_main_coin(cls, contract_address):
        new_id = 1
        result_db: list[dict] = _get_data_coin_local_db(table='mainCoin')
        if result_db:
            last_result_db = result_db[-1]
            old_id = last_result_db['mainCoinId']
            for main_coins_db in result_db:
                if contract_address == main_coins_db['contractAddress']:
                    cls.coin_id = main_coins_db['mainCoinId']
                    cls.name = main_coins_db['name']
                    cls.symbol = main_coins_db['symbol']
                    cls.contract_address = main_coins_db['contractAddress']
                    cls.decimals = main_coins_db['decimals']
                    cls.supply = main_coins_db['supply']
                    break
            if cls.coin_id is None:
                new_id = old_id + 1

        if cls.coin_id is None:
            coin_helper = RouterHelper()
            info_coin = coin_helper.get_coin_info(token_address=contract_address, get_full=True)
            if info_coin.get('error'):
                raise TypeError("\n !! Не установлена информация MainCoin !!\n")
            cls.coin_id = new_id
            cls.name = info_coin['name']
            cls.symbol = info_coin['symbol']
            cls.contract_address = contract_address
            cls.decimals = info_coin['decimals']
            cls.supply = info_coin['supply']


class Coin:
    def __init__(self, coin_id, name, symbol, status, circulating_supply,
                 contract_address, decimals, chain, supply,
                 launch_date, update_date_supply, is_updated_supply, use_db):
        self.main_coin = MainCoin

        self.coin_id = int(coin_id)
        self.name = name
        self.symbol = symbol
        self.status = status
        self.contract_address = contract_address
        self.decimals = decimals
        self.chain = chain
        self.launch_date = launch_date

        self.supply = supply
        if self.supply == 'None':
            self.supply = None
        self.circulating_supply = circulating_supply
        if self.circulating_supply == 'None':
            self.circulating_supply = '0'

        self.update_date_supply = update_date_supply
        self.is_updated_supply = is_updated_supply

        self.coin_reserves = None
        self.price_update_date = None

        self.price = None
        self.price_reduced_volume = None
        self.one_day_comparison = Decimal(0.0)
        self.market_cap = None

        self.error_reserves_coins: dict | None = None
        self.error_price: dict | None = None

        if use_db == "coinmooner":
            self.set_error_reserves_coins()

    def set_reserves_pair_coin(self, w3: Web3):
        router_helper_reserves = RouterHelper(w3=w3, )
        reserves = router_helper_reserves.get_reserves(self.main_coin.contract_address, self.contract_address)
        if isinstance(reserves, list):
            self.main_coin.reserves = reserves[0]
            self.coin_reserves = reserves[1]
        else:
            if '403 Client Error' in reserves['error']:
                return 'restart'
            reserves['mainCoinId'] = self.main_coin.coin_id
            reserves['coinId'] = self.coin_id
            self.error_reserves_coins = reserves

    def set_error_reserves_coins(self):
        result_err = _get_data_coin_local_db(
            table='error_reserves', where=f"coinId = {self.coin_id} AND mainCoinId = {self.main_coin.coin_id}"
        )
        if result_err:
            self.error_reserves_coins = result_err[-1]

    def set_supply_coin(self, w3: Web3 | None = None):
        coin_helper = RouterHelper(w3=w3)
        info_coin = coin_helper.get_coin_info(
            token_address=self.contract_address,
            input_decimals=self.decimals,
            get_total_supply=True,
            get_circulating_supply=True
        )
        if info_coin.get('error'):
            if '403 Client Error' in info_coin['error']:
                return 'restart'
            self.supply = None
            self.update_date_supply = datetime.now().strftime('%Y-%m-%d')
            self.is_updated_supply = 0
            return info_coin
            # raise TypeError(info_coin['error'])
        else:
            if info_coin.get('decimals') is not None:
                self.decimals = info_coin['decimals']
            self.circulating_supply = info_coin['circulating_supply']
            self.supply = info_coin['supply']
            self.update_date_supply = datetime.now().strftime('%Y-%m-%d')
            self.is_updated_supply = 1

    def set_market_cap(self):
        if self.supply is None or self.circulating_supply is None:
            return None
        count_token = 1
        self.market_cap = (Decimal(count_token) / Decimal(self.price)) * Decimal(self.circulating_supply)

    def set_price(self):
        if self.error_reserves_coins or self.coin_reserves in (None, 0):
            return None
        # p1 = (73.8 / 100) + (0.25 / 100)
        p1 = 0.26 / 100
        min_amount_x = 0.00001  # Пример количества входного актива
        amount_x = 1
        reserve_x = self.main_coin.reserves  # резерв входного актива
        reserve_y = self.coin_reserves  # резерв выходного актива
        try:
            price = (Decimal(reserve_y) / 10 ** self.decimals) / (
                    Decimal(reserve_x) / (Decimal(ETHER * amount_x)))
            self.price = Decimal(price) - (Decimal(price) * Decimal(p1))

            price_reduced_volume = (Decimal(reserve_y) / 10 ** self.decimals
                                    ) / (Decimal(reserve_x) / (Decimal(ETHER * min_amount_x)))
            self.price_reduced_volume = Decimal(price_reduced_volume) - (Decimal(price_reduced_volume) * Decimal(p1))

            self.price_update_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

        except Exception as error1:
            self.error_price = {
                "errorGetPrice": str(error1),
                "main_coin": self.main_coin.symbol,
                "coin_symbol": self.symbol,
                "coin_id": self.coin_id,
                "coin_contract_address": self.contract_address
            }

    def get_update_data_for_table_coin(self, one_column: str | None = None):
        dict_data_table_coin = {
            "updateDateSupply": self.update_date_supply, "isUpdatedSupply": self.is_updated_supply,
            "supply": self.supply, "circulatingSupply": self.circulating_supply, "decimals": self.decimals,
        }
        if one_column:
            return {key: value for key, value in dict_data_table_coin.items() if key == one_column}
        if dict_data_table_coin['decimals'] is None:
            del dict_data_table_coin['decimals']

        return dict_data_table_coin

    def get_data_for_table_price(self):
        if self.price is not None:
            dict_data_table_price = {
                "coinId": self.coin_id, "mainCoinId": self.main_coin.coin_id, "pairPrice": self.price,
                "oneDayComparison": self.one_day_comparison}

            return dict_data_table_price

    def get_data_for_table_market_cap(self):
        if self.market_cap is not None:
            dict_data_table_price = {
                "coinId": self.coin_id, "mainCoinId": self.main_coin.coin_id, "marketCapValue": self.market_cap,
                }
            return dict_data_table_price

    def get_info_coin_print(self):
        print(f"\n{self.coin_id=}")
        print(f"{self.contract_address=}")
        print(f"{self.status=}")
        print(f"{self.symbol=}")
        print(f"{self.supply=}\n{self.circulating_supply=}")
        print(f"{self.is_updated_supply=}\n{self.update_date_supply=}")
        print(f"{self.price_update_date=}\n{self.price=}\n{self.market_cap=}")
        print(f"{self.decimals=}\n{self.launch_date=}")
        print(f"{self.main_coin.reserves=}\n{self.coin_reserves=}")
        print(f"{self.error_reserves_coins=}")
        print(f"{self.error_price=}")
        print('==' * 40)


# if __name__ == '__main__':
#     query2 = f"""
#                     SELECT pairPrice, createdOn
#                     FROM price
#                     WHERE mainCoinId = {1} AND pairPrice != 0 AND coinId = {7}
#                     ORDER BY createdOn;
#                 """
#     data_db = _get_data_coin_local_db(input_query=query2)
#     result_db2 = data_db[-1]['pairPrice']
#     print(f"{result_db2=} / {type(result_db2)}")
