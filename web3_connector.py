import time
from web3 import Web3
from web3.middleware import geth_poa_middleware


class Web3Conn:
    def __init__(self):
        self.w3: Web3 | None = None
        self.node_url = 'https://bsc-dataseed1.binance.org/'
        self.proxy_url = 'http://user130949:fduqey@146.19.185.64:6380'

    def get_w3(self, proxy=False) -> Web3:
        count_error_conn = 0
        while True:
            if not proxy:
                self.w3 = Web3(Web3.HTTPProvider(self.node_url))
            else:
                self.w3 = Web3(Web3.HTTPProvider(self.node_url, request_kwargs={
                    "proxies": {'https': self.proxy_url, 'http': self.proxy_url}
                }))

            if self.w3.is_connected():
                print(f"Подключено к ноде: {self.node_url}")
                break
            else:
                print(f"[ {count_error_conn} ] Не удалось подключиться к ноде ... Переподключение.")
                time.sleep(30)
                count_error_conn += 1
                if count_error_conn > 3:
                    exit()

        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        return self.w3
