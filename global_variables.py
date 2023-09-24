import os
import toolbox


class GlobalVariables:
    path_file_launch_date_set_supply_coin = 'launch_date_set_supply_coin.bin'
    if os.path.isfile(path_file_launch_date_set_supply_coin):
        launch_date_set_supply_coin = toolbox.download_pickle_data(path_file_launch_date_set_supply_coin).__next__()
    else:
        launch_date_set_supply_coin = None

    limit_local_db = 1000
    number_sleep = 15
    path_count_start = 'count_start.txt'

    table_name_price = 'price'
    table_name_main_coin = 'mainCoin'
    table_name_coin = 'coin'
    table_name_coin_error = 'error_reserves'
    table_name_market_cap = 'marketCap'

    columns_list = [
        'id', 'name', 'symbol', 'status', 'decimals',
        'contractAddress', 'chain', 'supply', 'launchDate',
    ]

    my_tables_list = [
        table_name_price, table_name_main_coin, table_name_coin, table_name_coin_error, table_name_market_cap
    ]
    use_db_local = "coinmooner"
    use_db_mooner = "MOONER_DEV"

    current_directory = os.path.dirname(__file__)
    dir_name_config_db = "db_config"
    file_name_db_config_local = "db_config_local.json"
    file_name_db_config_dev = "db_config_mooner_dev.json"

    path_db_config_local = os.path.join(current_directory, dir_name_config_db, file_name_db_config_local)
    path_db_config_dev = os.path.join(current_directory, dir_name_config_db, file_name_db_config_dev)

    db_config_mooner_local = toolbox.download_json_data(path_file=path_db_config_local)
    db_config_mooner_dev = toolbox.download_json_data(path_file=path_db_config_dev)
