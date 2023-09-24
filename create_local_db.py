import aiomysql


async def create_db(db_config_local):
    async with aiomysql.connect(**db_config_local) as conn:
        conn: aiomysql.Connection
        async with conn.cursor() as cursor:
            cursor: aiomysql.Cursor
            # Создаем базу данных
            await cursor.execute("CREATE DATABASE IF NOT EXISTS coinmooner")

            # Подключаемся к созданной базе данных
            await conn.select_db("coinmooner")

            # Создаем таблицу coin
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS coin (
                    id INT PRIMARY KEY NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    symbol VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    chain VARCHAR(30) NOT NULL,
                    supply VARCHAR(255),
                    isUpdatedSupply TINYINT(1) DEFAULT 0,
                    contractAddress VARCHAR(255) NOT NULL,
                    circulatingSupply VARCHAR(255),
                    decimals INT,
                    launchDate DATE NOT NULL,
                    updateDateSupply DATE
                )
            """)

            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS mainCoin (
                    mainCoinId INT NOT NULL,
                    name VARCHAR(30) NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    supply VARCHAR(255),
                    contractAddress VARCHAR(255) NOT NULL,
                    decimals INT,
                    PRIMARY KEY (mainCoinId)
                )
            """)

            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_reserves (
                    id INT AUTO_INCREMENT NOT NULL,
                    error TEXT NOT NULL,
                    mainCoinId INT NOT NULL,
                    coinId INT NOT NULL,
                    createdOn DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    PRIMARY KEY (id),
                    FOREIGN KEY (coinId) REFERENCES coin(id),
                    FOREIGN KEY (mainCoinId) REFERENCES mainCoin(mainCoinId)
                )
            """)

            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS price (
                    id INT NOT NULL AUTO_INCREMENT,
                    pairPrice DECIMAL(65, 25) NOT NULL,
                    oneDayComparison DECIMAL(65, 25),
                    mainCoinId INT NOT NULL,
                    coinId INT NOT NULL,
                    createdOn DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    PRIMARY KEY (id),
                    FOREIGN KEY (coinId) REFERENCES coin(id),
                    FOREIGN KEY (mainCoinId) REFERENCES mainCoin(mainCoinId)
                )
            """)

            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS marketCap (
                    id INT NOT NULL AUTO_INCREMENT,
                    marketCapValue DECIMAL(65, 25) NOT NULL,
                    marketCapValueStr VARCHAR(255) DEFAULT NULL,
                    coinId INT NOT NULL,
                    mainCoinId INT NOT NULL,
                    createdOn DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    PRIMARY KEY (id),
                    FOREIGN KEY (coinId) REFERENCES coin(id),
                    FOREIGN KEY (mainCoinId) REFERENCES mainCoin(mainCoinId)
                )
            """)


if __name__ == '__main__':
    import asyncio
    import toolbox

    db_config_mooner_local = toolbox.download_json_data(path_file="db_config/db_config_local.json")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_db(db_config_mooner_local))
