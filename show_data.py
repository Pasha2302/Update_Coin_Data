import os
import time
from datetime import datetime, timedelta
from asyncio import AbstractEventLoop

import toolbox
from async_mysql_database import AsyncMySQLManager


use_db_local = "coinmooner"
use_db_mooner = "MOONER_DEV"

db_config_mooner_dev = toolbox.download_json_data(path_file="db_config/db_config_mooner_dev.json")
db_config_mooner_local = toolbox.download_json_data(path_file="db_config/db_config_local.json")

print(db_config_mooner_dev)
print(db_config_mooner_local)
db_coinmooner = AsyncMySQLManager(db_config_mooner_dev, use_db=use_db_mooner)
db_coin_local = AsyncMySQLManager(db_config_mooner_local, use_db=use_db_local)

table_name_price = 'price'
table_name_coin = 'coin'
table_name_coin_error = 'error_reserves'
table_name_main_coin = 'mainCoin'
table_name_market_cap = 'marketCap'


my_tables_list = [table_name_price, table_name_coin, table_name_coin_error, table_name_main_coin, table_name_market_cap]
columns_list = ['id', 'name', 'symbol', 'status', 'contractAddress', 'chain', 'supply', 'launchDate']


async def show_type_columns(table_name, external=False, internal=False):
    datas = []
    query_str = f"DESCRIBE {table_name};"
    if external:
        datas = await db_coinmooner.execute_query(query=query_str, fetch=True)
    if internal:
        datas = await db_coin_local.execute_query(query=query_str, fetch=True)
    for data in datas:
        # if data['Field'] in columns_list:
        #     print(data)
        # if data['Type'] == 'date':
        #     print(data)
        print(data)


async def get_unique_coin_id_from_table(table_name: str, main_coin_id: int):
    select_query = f"SELECT coinId FROM {table_name} WHERE mainCoinId = {main_coin_id}"
    unique_coin_id_list_dict = await db_coin_local.execute_query(select_query, fetch=True)

    unique_coin_id_list = {unique_coin_id['coinId'] for unique_coin_id in unique_coin_id_list_dict}
    print(f"Table [{table_name}]: {len(unique_coin_id_list)=}")
    return list(unique_coin_id_list)


async def execute_custom_sql_request():
    print(f"\n{'++' * 40}")
    # query = f"""
    #             SELECT marketCap.*, price.*
    #             FROM price
    #                 LEFT JOIN marketCap ON marketCap.coinId = price.coinId
    #             WHERE price.coinId = 35100 and price.mainCoinId = 2
    #             ORDER BY createdOn
    #         """
    # query = f"""
    #             SELECT marketCap.*, price.*
    #             FROM marketCap
    #                 LEFT JOIN price ON marketCap.coinId = price.coinId
    #                     AND marketCap.mainCoinId = price.mainCoinId
    #                     AND DATE(marketCap.createdOn) = DATE(price.createdOn)
    #             WHERE marketCap.coinId = 33716
    #             ORDER BY marketCap.createdOn
    #         """
    # query = f"""
    #             SELECT marketCap.*, price.*
    #             FROM price
    #                 LEFT JOIN marketCap ON marketCap.coinId = price.coinId
    #                     AND marketCap.mainCoinId = price.mainCoinId
    #                     AND DATE_FORMAT(marketCap.createdOn, '%Y-%m-%d %H:%i') =
    #                         DATE_FORMAT(price.createdOn, '%Y-%m-%d %H:%i')
    #             WHERE marketCap.coinId = 33716
    #             ORDER BY marketCap.createdOn
    #         """
    # query = f"""
    #             SELECT *
    #             FROM error_reserves
    #             WHERE error REGEXP '403 Client Error'
    #         """
    # query = f"""
    #             SELECT *
    #             FROM error_reserves
    #             WHERE mainCoinId = 1 AND error REGEXP '.+'
    #             ORDER BY createdOn
    #         """
    # query = f"""
    #             DELETE
    #             FROM error_reserves
    #             WHERE error REGEXP 'Max retries exceeded with url';
    #         """
    query = f"SELECT * FROM price WHERE mainCoinId = 1 AND DATE(createdOn) = '2023-09-24' ORDER BY createdOn"
    # query = f"SELECT * FROM price WHERE coinId = 5770 AND mainCoinId = 1 ORDER BY createdOn"
    # query = f"SELECT * FROM price WHERE mainCoinId = 1 AND pairPrice = 0 ORDER BY createdOn"
    # query = f"SELECT * FROM marketCap WHERE mainCoinId = 1 AND DATE(createdOn) = '2023-09-22' ORDER BY createdOn"
    # query = f"SELECT * FROM marketCap WHERE coinId = 33716 ORDER BY createdOn"
    # query = f"SELECT * FROM marketCap WHERE marketCapValueStr"

    # query = f"SELECT * FROM marketCap"
    # query = f"SELECT * FROM coin WHERE decimals is NULL"
    # query = f"SELECT * FROM coin WHERE contractAddress = '0x9641c1eee00471f7da822167f6cf77202356179a'"
    # query = f"SELECT * FROM coin WHERE decimals = 0"
    # query = f"SELECT * FROM coin WHERE circulatingSupply = 0"
    # query = f"SELECT * FROM coin WHERE DATE(updateDateSupply) = '2023-09-24'"
    # query = f"SELECT * FROM error_reserves WHERE mainCoinId = 1"
    result_coin_prices = await db_coin_local.execute_query(query=query, fetch=True)
    # await db_coin_local.save_data_db()

    total_rows = len(result_coin_prices)
    for data in result_coin_prices:
        for k, v in data.items():
            print(f"{k}: < {v} >     ( {type(v)} )")
        print('==' * 40)
    print(f"Всего записей: {total_rows=}")

    # new_data = [{key: str(value) for key, value in data_dict.items()} for data_dict in result_coin_prices]
    # toolbox.save_json_data(json_data=new_data, path_file="check_data_db.json")


async def start_show_data_tables():
    # await db_coinmooner.connect()
    # await show_type_columns(table_name=table_name_coin, internal=True)
    # await db_coinmooner.show_table_data(tables=[table_name_coin], columns=columns_list, limit=100)
    # await db_coinmooner.show_table_data(tables=[table_name_coin], limit=100)

    # await db_coin_local.show_table_data(tables=[table_name_coin])
    # await db_coin_local.show_table_data(tables=[table_name_coin_error])
    # await db_coin_local.show_table_data([table_name_price])
    # ================================================================================================================ #
    print('--' * 40)
    await execute_custom_sql_request()
    # print('--' * 40)
    # await get_unique_coin_id_from_table(table_name='marketCap', main_coin_id=1)
    # await get_unique_coin_id_from_table(table_name='price', main_coin_id=1)
    # ================================================================================================================ #
    # Выбираем последнюю строку из таблицы
    # query = f"SELECT * FROM {table_name_price} ORDER BY id DESC LIMIT 1"
    # last_row = await db_coinmooner.execute_query(query=query, fetch=True)
    # print(f"{last_row=}\n\n")
    # ================================================================================================================ #

    # current_date = datetime.now()  #.strftime('%Y-%m-%d %H:%M:%S.%f')
    # toolbox.save_pickle_data(data_pickle=current_date, path_file="pickle_date_test.bin")

    # gen_data = toolbox.download_pickle_data(path_file="pickle_date_test.bin")
    # for data in gen_data:
    #     time_difference: timedelta = datetime.now() - data
    #     print(type(time_difference))
    #     print(f"{time_difference=}")


if __name__ == '__main__':
    with toolbox.create_loop() as loop:
        loop.run_until_complete(db_coin_local.connect())
        loop: AbstractEventLoop
        try:
            loop.run_until_complete(start_show_data_tables())
        finally:
            loop.run_until_complete(db_coinmooner.disconnect())
            loop.run_until_complete(db_coin_local.disconnect())
            time.sleep(0.35)
