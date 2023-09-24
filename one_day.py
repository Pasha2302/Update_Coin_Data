import asyncio
import datetime

from Update_Coin_Data.async_mysql_database import AsyncMySQLManager
from global_variables import GlobalVariables as Gv

minutes_in_a_day = 1440
minutes_in_a_hours = 60
db_coin_mooner_loc: AsyncMySQLManager | None = None


async def get_unique_coin_id_from_table_price(main_coin_id: int):
    await db_coin_mooner_loc.connect()

    select_query = f"SELECT coinId FROM price WHERE mainCoinId = {main_coin_id} AND pairPrice != 0;"
    unique_coin_id_list_dict = await db_coin_mooner_loc.execute_query(select_query, fetch=True)

    unique_coin_id_list = {unique_coin_id['coinId'] for unique_coin_id in unique_coin_id_list_dict}
    print(f"\n{len(unique_coin_id_list)=}\n")
    return tuple(unique_coin_id_list)


def time_difference_check(time_difference: datetime.timedelta, time_difference_minutes: int):
    if minutes_in_a_day - 120 < time_difference_minutes <= minutes_in_a_day and time_difference.days == 0:
        return True
    elif time_difference.days == 1 and (time_difference_minutes <= minutes_in_a_hours * 4):
        return True


async def calculate_and_update_one_day_comparison(main_coin_id: int = 1):
    coins_id = await get_unique_coin_id_from_table_price(main_coin_id)

    for coin_id in coins_id:
        # Запрос для извлечения записей, которые нужно обновить, упорядоченных по времени создания
        select_query = f"""
            SELECT id, pairPrice, createdOn
            FROM price 
            WHERE mainCoinId = {main_coin_id} AND pairPrice != 0 AND coinId = {coin_id} ORDER BY createdOn
        """
        rows = await db_coin_mooner_loc.execute_query(select_query, fetch=True)

        # print(f"{len(rows)=}")
        for i in range(len(rows)):
            row_i = rows[i]
            price_id_i, pair_price_i, created_date_i = row_i.values()
            for j in range(i + 1, len(rows)):
                row_j = rows[j]
                price_id_j, pair_price_j, created_date_j = row_j.values()

                # Рассчитываем разницу во времени между датами
                time_difference = created_date_j - created_date_i
                time_difference_minutes: int = time_difference.seconds / 60
                if coin_id == 33716:
                    print(f"index: {i=}")
                    print(f"index: {j=}")
                    print(f"{time_difference=}")
                    print(f"{time_difference_minutes=}")
                    print('--' * 40)
                # Проверяем, прошел ли один день между датами
                # if time_difference.days == 1 or (
                #         minutes_in_a_day - 120 < time_difference_minutes <= minutes_in_a_day
                # ):
                if time_difference_check(time_difference, time_difference_minutes):
                    one_day_comparison = pair_price_j - pair_price_i

                    if coin_id == 33716:
                        print('$$' * 40)
                        print(f"index: {i=}")
                        print(f"index: {j=}")
                        print(f"{time_difference.days=}")
                        print(f"{time_difference_minutes} minutes")
                        print(f"{one_day_comparison=}")
                        print('--' * 40)

                    # Обновляем значение oneDayComparison в базе данных для записи с price_id_i
                    update_query = f"UPDATE price SET oneDayComparison = {one_day_comparison} WHERE id = {price_id_j}"
                    await db_coin_mooner_loc.execute_query(update_query)
        # print('==' * 40)
    await db_coin_mooner_loc.save_data_db()
    await db_coin_mooner_loc.disconnect()


async def reset_column_one_day_comparison():
    await db_coin_mooner_loc.connect()
    query = "UPDATE price SET oneDayComparison = 0.0"
    await db_coin_mooner_loc.execute_query(query)
    await db_coin_mooner_loc.save_data_db()


async def main():
    global db_coin_mooner_loc
    db_coin_mooner_loc = AsyncMySQLManager(Gv.db_config_mooner_local, use_db=Gv.use_db_local)

    # await reset_column_one_day_comparison()
    await calculate_and_update_one_day_comparison()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.run_until_complete(db_coin_mooner_loc.disconnect())
    # "mysqldump -u pavelpc -p coinmooner > coinmooner_backup.sql"
