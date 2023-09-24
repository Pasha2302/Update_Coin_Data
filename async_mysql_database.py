import aiomysql
import asyncio


class AsyncMySQLManager:
    def __init__(self, db_config: dict, use_db: str):
        self.db_config = db_config
        self.use_db = use_db
        self.connection: aiomysql.Connection | None = None

    async def connect(self):
        self.connection = await aiomysql.connect(**self.db_config)
        await self.connection.select_db(self.use_db)

    async def disconnect(self):
        if self.connection:
            self.connection.close()
            await asyncio.sleep(.25)

    async def save_data_db(self):
        await self.connection.commit()

    async def execute_query(self, query, fetch=False):
        # dictionary=True включает возвращение результатов в виде словарей
        async with self.connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query)
            if fetch:
                result = await cursor.fetchall()
                return result
            # else:
            #     await self.connection.commit()

    async def get_tables(self):
        query = "SHOW TABLES"
        tables = await self.execute_query(query, fetch=True)
        return tables

    async def check_id_in_db(self, table_name, target_id):
        query = f"SELECT id FROM {table_name} WHERE id = %s"
        async with self.connection.cursor() as cursor:
            # Выполняем SQL-запрос для поиска ID в базе данных
            await cursor.execute(query, (target_id,))
            result = await cursor.fetchone()
            if result:
                return True

    async def update_data(self, table_name: str, column_values: dict, where: str | None = None, update_date=False):
        pref_query = ''
        data_update = [f"{column} = '{value}'" for column, value in column_values.items()]
        if update_date:
            data_update.append("update_date = CURRENT_TIMESTAMP(6)")
        set_values = ", ".join(data_update)
        if where:
            pref_query = f" WHERE {where}"
        query = f"UPDATE {table_name} SET {set_values}{pref_query}"
        await self.execute_query(query)

    async def get_number_rows_table(self, table_name):
        # Получить количество строк в таблице
        query = f"SELECT COUNT(*) FROM {table_name}"
        number_rows = await self.execute_query(query, fetch=True)
        return number_rows[0]['COUNT(*)']

    async def get_data_from_table(
            self, table_name: str,
            columns: list[str] | None = None,
            limit=None,
            offset=None
    ):
        columns_str = "* "
        if columns:
            columns_str = ", ".join(columns)
        query = f"SELECT {columns_str.strip(',')} FROM {table_name}"
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"
        data = await self.execute_query(query, fetch=True)
        return data

    async def drop_table(self, table_name):
        query = f"DROP TABLE IF EXISTS {table_name}"
        await self.execute_query(query)

    async def insert_data(self, table_name, column_values):
        columns = ", ".join([key for key in column_values.keys()])
        values = ", ".join(["%s" for _ in column_values.values()])
        query = f"INSERT INTO {table_name} ({columns.strip(',')}) VALUES ({values.strip(',')})"
        values_list = [value for value in column_values.values()]

        async with self.connection.cursor() as cursor:
            try:
                await cursor.execute(query, values_list)
            except Exception as error_duplicate:
                if 'Duplicate entry' in str(error_duplicate):
                    return 'Duplicate entry'
                else:
                    raise error_duplicate

    async def show_table_data(self, tables: list[str], columns: list[str] | None = None, limit: int = None):
        datas = []
        for table_name in tables:
            if table_name:
                print(f"\n<<<<<< Table {table_name.capitalize()} >>>>>>")
                if columns and isinstance(columns, list):
                    datas = await self.get_data_from_table(table_name, columns, limit=limit)
                else:
                    datas = await self.get_data_from_table(table_name, limit=limit)
                for row_dict in datas:
                    for k, v in row_dict.items():
                        print(f"{k}: {v}")
                    print('==' * 40)
            print(f"Всего получено записей из таблицы < {table_name} >: {len(datas)}")
            print('**' * 40)

    async def add_column_to_table(self, table_name, new_column_name, type_column):
        # Замените 'your_table' на имя вашей таблицы и 'new_column' на имя новой колонки и ее тип данных.
        alter_query = f"ALTER TABLE {table_name} ADD {new_column_name} {type_column}"
        await self.execute_query(alter_query)
        await self.save_data_db()

    async def rename_column(self, table_name, old_column, new_column_and_type):
        alter_query = f"ALTER TABLE {table_name} CHANGE {old_column} {new_column_and_type}"
        await self.execute_query(alter_query)
        await self.save_data_db()

    async def remove_column_from_table(self, table_name, column_to_remove):
        # Замените 'your_table' на имя вашей таблицы и 'column_to_remove' на имя колонки, которую нужно удалить.
        alter_query = f"ALTER TABLE {table_name} DROP COLUMN {column_to_remove}"
        await self.execute_query(alter_query)
        await self.save_data_db()


async def main():
    await db_coin_local.connect()

    await db_coin_local.drop_table(table_name='marketCap')

    # await db_coin_local.rename_column(
    #     table_name='marketCap', old_column='marketCap', new_column_and_type="marketCapValue DECIMAL(65, 25) NOT NULL"
    # )
    # await db_coin_local.add_column_to_table(
    #     table_name='marketCap', new_column_name='marketCapValueStr', type_column='VARCHAR(255) DEFAULT NULL'
    # )


if __name__ == '__main__':
    import time
    import toolbox
    from asyncio import AbstractEventLoop

    use_db_local = "coinmooner"
    use_db_mooner = "MOONER_DEV"

    # db_config_mooner_dev = toolbox.download_json_data(path_file="db_config/db_config_mooner_dev.json")
    db_config_mooner_dev = toolbox.download_json_data(path_file="db_config/db_config_local.json")
    print(db_config_mooner_dev)
    db_coin_local = AsyncMySQLManager(db_config_mooner_dev, use_db=use_db_local)
    with toolbox.create_loop() as loop:
        loop: AbstractEventLoop
        try:
            loop.run_until_complete(main())
        finally:
            loop.run_until_complete(db_coin_local.disconnect())
            time.sleep(0.35)
