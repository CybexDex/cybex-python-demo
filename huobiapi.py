import ccxt
import json


class HuobiApi:

    def __init__(self, key, secret):
        config = {'apiKey': key, 'secret': secret, 'enableRateLimit': True}
        json_str = json.dumps(config)
        print(json_str)
        self.exchange = ccxt.huobipro(config)
        self.exchange.load_markets()

    def get_ohlcv(self, symbol, start, end):
        return self.exchange.fetch_ohlcv(symbol, since=start)

    def get_order_book(self, symbol):
        return self.exchange.fetch_order_book(symbol, limit=10)