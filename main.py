import os
import sys
import time
import datetime
import asyncio
import concurrent.futures
from asyncio import AbstractEventLoop

import toolbox
from async_mysql_database import AsyncMySQLManager
from coin_1 import Coin, MainCoin
from create_local_db import create_db
from web3_connector import Web3Conn

from global_variables import GlobalVariables as Gv

log_file = open('output.log', 'w')
# Перенаправляем стандартный вывод в файл
sys.stdout = log_file


async def create_thread_pool_coin_metad(name_metad_coins: str, tasks_coins: tuple[Coin], *args):
    # --------------------------------------------------------------------------------------------------------------- #
    # Создайте пул потоков (можно также использовать пул процессов)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Запустите функции в отдельных потоках и получите объекты Future для отслеживания их выполнения
        if name_metad_coins == 'get_reserves_pair_coin':
            futures = [
                loop.run_in_executor(executor, coin_m.set_reserves_pair_coin, *args)
                for coin_m in tasks_coins if coin_m.error_reserves_coins is None
            ]

        elif name_metad_coins == 'set_supply_coin':
            futures = [
                loop.run_in_executor(executor, coin_m.set_supply_coin, *args) for coin_m in tasks_coins
            ]

        elif name_metad_coins == 'set_market_cap':
            futures = [
                loop.run_in_executor(executor, coin_m.set_market_cap)
                for coin_m in tasks_coins if coin_m.price is not None
            ]
        # ----------------------------------------------------------------------------------------------------------- #
        count_correct_coins = len(futures)
        count_error_coins = len(tasks_coins) - count_correct_coins
        print(f"\n[Metad: {name_metad_coins}]\n"
              f"Монет для обновления данных: {count_correct_coins} из {len(tasks_coins)}\n"
              f"Монет не получивших значение: {count_error_coins}\n{'~~' * 40}")
        if count_correct_coins < 500:
            Gv.number_sleep = 3
        else:
            Gv.number_sleep = 15

        result_reserves = await asyncio.gather(*futures)
        for res in result_reserves:
            if res:
                if 'restart' == res:
                    return res
                toolbox.save_json_complementing(json_data=res, path_file='error_coins.json', ind=True)

        if name_metad_coins == 'get_reserves_pair_coin':
            for coin_p in tasks_coins:
                check_result_price = coin_p.set_price()
                if isinstance(check_result_price, dict):
                    toolbox.save_json_complementing(
                        json_data=check_result_price,
                        path_file='error_coins_set_price.json',
                        ind=True
                    )


def get_tasks_coins(datas_coinsmooner):
    full_list_tasks = []

    for data_coin in datas_coinsmooner:
        if 'https://' in data_coin['contractAddress']:
            data_coin['contractAddress'] = data_coin['contractAddress'].split('/')[-1]
        coin = Coin(
            coin_id=data_coin['id'], name=data_coin['name'], symbol=data_coin['symbol'], status=data_coin['status'],
            contract_address=data_coin['contractAddress'].strip(), decimals=data_coin['decimals'],
            chain=data_coin['chain'], supply=data_coin['supply'], launch_date=data_coin['launchDate'],
            use_db=db_coin_mooner_loc.use_db, update_date_supply=data_coin['updateDateSupply'],
            is_updated_supply=data_coin['isUpdatedSupply'], circulating_supply=data_coin['circulatingSupply']
        )
        full_list_tasks.append(coin)

    return tuple(full_list_tasks)


async def check_start_set_supply_coin(current_date, list_metad_coins):
    if not Gv.launch_date_set_supply_coin:
        list_metad_coins = ["set_supply_coin"]
    else:
        old_date_start_set_market_cap = Gv.launch_date_set_supply_coin
        date_difference = current_date - old_date_start_set_market_cap
        if date_difference.days >= 7:
            list_metad_coins = ["set_supply_coin"]

    if "set_supply_coin" in list_metad_coins:
        print(f"\nУстановлен метод: [set_supply_coin]")
        await db_coin_mooner_loc.update_data(
            table_name=Gv.table_name_coin,
            column_values={"circulatingSupply": "None"}
        )
        await db_coin_mooner_loc.save_data_db()
        Gv.limit_local_db = 100

    return list_metad_coins


async def start_get_coins_data(
        number_rows_local_db, one_metad_coins: str | None = None):
    current_date = datetime.datetime.now()
    count_coins_data_iterations = 0
    stop_coins_data_iterations = -1  # Количество циклов до остановки.

    list_metad_coins = ["get_reserves_pair_coin", "set_market_cap"]
    list_metad_coins = await check_start_set_supply_coin(current_date, list_metad_coins)
    if one_metad_coins:
        list_metad_coins = [one_metad_coins, ]

    w3 = Web3Conn().get_w3()
    Gv.columns_list.extend(('updateDateSupply', 'isUpdatedSupply', 'circulatingSupply'))

    for offset in range(0, number_rows_local_db, Gv.limit_local_db):
        number_sleep_limit = 60
        print(f"{offset=}")
        datas_coinsmooner = await db_coin_mooner_loc.get_data_from_table(
            table_name=Gv.table_name_coin,
            columns=Gv.columns_list,
            limit=Gv.limit_local_db,
            offset=offset
        )

        tasks_coins = get_tasks_coins(datas_coinsmooner)
        # ============================================================================================================ #
        for name_metad_coins in list_metad_coins:
            while True:
                check_res = await create_thread_pool_coin_metad(name_metad_coins, tasks_coins, w3)
                if check_res == 'restart':
                    print(f"\n<<< Лимит запросов к ноде исчерпан, ожидание: {number_sleep_limit} сек. >>>")
                    time.sleep(number_sleep_limit)
                    w3 = Web3Conn().get_w3()
                else:
                    break

            if name_metad_coins != 'set_market_cap':
                print(
                    f"Время ожидания для следующий итерации {Gv.limit_local_db} монет: "
                    f"{Gv.number_sleep} sec.\n{'==' * 40}"
                )
                time.sleep(Gv.number_sleep)

        # ============================================================================================================ #
        if 'set_supply_coin' in list_metad_coins:
            for coin_s in tasks_coins:
                data_table_coin = coin_s.get_update_data_for_table_coin()
                await db_coin_mooner_loc.update_data(
                    table_name=Gv.table_name_coin,
                    column_values=data_table_coin,
                    where=f"id = {coin_s.coin_id}")

        # ------------------------------------------------------------------------------------------------------------ #
        if 'get_reserves_pair_coin' in list_metad_coins:
            for coin_p in tasks_coins:
                coin_p: Coin
                data_table_price = coin_p.get_data_for_table_price()
                if data_table_price:
                    try:
                        await db_coin_mooner_loc.insert_data(
                            table_name=Gv.table_name_price, column_values=data_table_price)
                    except Exception as error_insert_data_price:
                        if "Out of range value for column 'pairPrice'" in str(error_insert_data_price):
                            print(f"\n!!! ERROR_PRICE: {error_insert_data_price}\n"
                                  f"{coin_p.get_info_coin_print()}")
                            exit()
                        else:
                            raise error_insert_data_price

                if coin_p.error_reserves_coins:
                    await db_coin_mooner_loc.insert_data(
                        table_name=Gv.table_name_coin_error, column_values=coin_p.error_reserves_coins)

        # ------------------------------------------------------------------------------------------------------------ #
        if 'set_market_cap' in list_metad_coins:
            for coin_m in tasks_coins:
                data_table_market_cap = coin_m.get_data_for_table_market_cap()
                if data_table_market_cap:
                    try:
                        await db_coin_mooner_loc.insert_data(
                            table_name=Gv.table_name_market_cap, column_values=data_table_market_cap)
                    except Exception as error_market_cap:
                        if "Out of range value for column" in str(error_market_cap):
                            print("!!! Out of range value for column 'marketCapValue' ")
                            coin_m.get_info_coin_print()
                            data_table_market_cap['marketCapValueStr'] = str(data_table_market_cap['marketCapValue'])
                            data_table_market_cap['marketCapValue'] = 0.0
                            await db_coin_mooner_loc.insert_data(
                                table_name=Gv.table_name_market_cap, column_values=data_table_market_cap)
                        else:
                            raise TypeError(str(error_market_cap))

        # ------------------------------------------------------------------------------------------------------------ #
        await db_coin_mooner_loc.save_data_db()

        count_coins_data_iterations += 1
        if count_coins_data_iterations == stop_coins_data_iterations:
            break

    if 'set_supply_coin' in list_metad_coins:
        toolbox.save_pickle_data(data_pickle=current_date, path_file=Gv.path_file_launch_date_set_supply_coin)


async def receive_coins_from_external_db(number_rows_external_db):
    limit = 2000

    for offset in range(0, number_rows_external_db, limit):
        print(f"{offset=}")

        datas_coinsmooner = await db_coin_mooner.get_data_from_table(
            table_name=Gv.table_name_coin,
            columns=Gv.columns_list,
            limit=limit,
            offset=offset
        )

        for data_mooner_coin in datas_coinsmooner:
            check_insert_coin = await db_coin_mooner_loc.insert_data(
                table_name=Gv.table_name_coin, column_values=data_mooner_coin)
            if check_insert_coin == 'Duplicate entry':
                pass
        await db_coin_mooner_loc.save_data_db()

    number_rows = await db_coin_mooner_loc.get_number_rows_table(table_name=Gv.table_name_coin)
    print(f"\n\nTable local Coin: {number_rows=}")

    return number_rows


async def start_receive_coins():
    await db_coin_mooner.connect()
    number_rows_external_db = await db_coin_mooner.get_number_rows_table(table_name=Gv.table_name_coin)
    number_rows_local_db = await db_coin_mooner_loc.get_number_rows_table(table_name=Gv.table_name_coin)
    print(f"{number_rows_local_db=}\n{number_rows_external_db=}")

    if number_rows_external_db != number_rows_local_db:
        number_rows_local_db = await receive_coins_from_external_db(number_rows_external_db)

    await db_coin_mooner.disconnect()
    return number_rows_local_db


async def main():
    # main_coin = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'  # WBNB
    main_coin = '0x55d398326f99059fF775485246999027B3197955'  # USDT

    count_start = 0
    if os.path.isfile(Gv.path_count_start):
        count_start = int(toolbox.download_txt_data(path_file=Gv.path_count_start).strip())
    if count_start == 0:
        await create_db(db_config_local=Gv.db_config_mooner_local)

    await db_coin_mooner_loc.connect()

    MainCoin.set_main_coin(contract_address=main_coin)
    check_main_coin = await db_coin_mooner_loc.insert_data(
        table_name=Gv.table_name_main_coin,
        column_values=MainCoin.get_data_for_table_main_coin())
    print(f"{check_main_coin=}")

    number_rows_local_db = await start_receive_coins()
    # await start_get_coins_data(number_rows_local_db, one_metad_coins="set_market_cap")
    await start_get_coins_data(number_rows_local_db)

    toolbox.save_txt_data(data_txt='1', path_file=Gv.path_count_start)


if __name__ == '__main__':

    db_coin_mooner = AsyncMySQLManager(Gv.db_config_mooner_dev, use_db=Gv.use_db_mooner)
    db_coin_mooner_loc = AsyncMySQLManager(Gv.db_config_mooner_local, use_db=Gv.use_db_local)

    with toolbox.create_loop() as loop:
        loop: AbstractEventLoop
        try:
            loop.run_until_complete(main())
        finally:
            loop.run_until_complete(db_coin_mooner.disconnect())
            loop.run_until_complete(db_coin_mooner_loc.disconnect())

    log_file.close()
