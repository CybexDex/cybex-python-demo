import configparser
import requests
from time import sleep, time
from binanceapi import BinanceRestful
from huobiapi import HuobiApi
from cybexapi import CybexRestful
from datetime import datetime
from enum import Enum

FAST_PERIOD = 12
SLOW_PERIOD = 26
SIGNAL_PERIOD = 9


sym_base = 'ETH'
sym_quote = 'USDT'
symbol = 'ETH/USDT'

class OrderStatus(Enum):
    New = '0'
    PartiallyFilled = '1'
    Filled = '2'
    Canceled = '4'
    PendingCancel = '6'
    Rejected = '8'
    PendingNew = 'A'


class Order:
    def __init__(self):
        self.seller = None
        self.order_sequence = 0
        self.order_status = OrderStatus.PendingNew
        self.sell_asset_id = None
        self.buy_asset_id = None
        self.sold = 0
        self.received = 0
        self.to_sell = 0
        self.to_receive = 0
        self.trx_id = ''

class BarData:
    def __init__(self):
        self.start_time = datetime.fromtimestamp(0)
        self.px_open = 0.0
        self.px_high = 0.0
        self.px_low = 0.0
        self.px_close = 0.0
        self.volume = 0.0
        self.end_time = datetime.fromtimestamp(0)
        self.sma_fast = 0
        self.sma_slow = 0
        self.ema_fast = 0
        self.ema_slow = 0
        self.macd = 0
        self.macd_signal = 0
        self.finalized = False


class OrderBook:
    def __init__(self):
        self.bids = []
        self.asks = []

    def get_best_bid(self):
        if len(self.bids) > 0:
            return self.bids[0]
        return None

    def get_best_ask(self):
        if len(self.asks) > 0:
            return self.asks[0]
        return None


class MarketDataManager:
    def __init__(self):
        self.bars = []
        self.order_book = OrderBook()
        self.best_bid = 0
        self.best_ask = 0

    def get_order_book(self):
        return self.order_book

    def is_new_bar(self, bar):
        if len(self.bars) == 0:
            return True
        return self.bars[-1].start_time < bar.start_time

    def update_bar_data(self, bar):
        if len(self.bars) == 0:
            self.bars.append(bar)
            print('insert a bar, current length', len(self.bars))
            return

        if self.is_new_bar(bar):
            self.bars.append(bar)
            print('insert a bar, current length', len(self.bars))
        elif self.bars[-1].start_time == bar.start_time:
            self.bars[-1] = bar

    def redo_sma(self):
        if SLOW_PERIOD > len(self.bars):
            return

        for i in range(SLOW_PERIOD, len(self.bars)):
            self.calc_sma(i)

    def redo_ema(self):
        for i in range(0, len(self.bars)):
            self.calc_ema(i)

    def calc_ema(self, index):
        if index == 0:
            return

        this_bar = self.bars[index]
        last_bar = self.bars[index-1]

        fast_k = 2 / (FAST_PERIOD + 1)
        slow_k = 2 / (SLOW_PERIOD + 1)
        signal_k = 2 / (SIGNAL_PERIOD + 1)

        this_bar.ema_fast = (this_bar.px_close - last_bar.ema_fast) * fast_k + last_bar.ema_fast
        this_bar.ema_slow = (this_bar.px_close - last_bar.ema_slow) * slow_k + last_bar.ema_slow
        this_bar.macd = this_bar.ema_fast - this_bar.ema_slow
        this_bar.macd_signal = (this_bar.macd - last_bar.macd_signal) * signal_k + last_bar.macd_signal

        print('calc_ema {0} {1:.4f} {2:.4f} {3:.4f} {4:.4f}'
              .format(index, this_bar.macd, this_bar.macd_signal, this_bar.ema_fast, this_bar.ema_slow))

    def calc_sma(self, index):
        if len(self.bars) <= SLOW_PERIOD or index > len(self.bars):
            return

        fast_sum = 0
        for i in range(index - FAST_PERIOD, index):
            fast_sum += self.bars[i].px_close

        fast_val = fast_sum / FAST_PERIOD

        slow_sum = 0
        for i in range(index - SLOW_PERIOD, index):
            slow_sum += self.bars[i].px_close

        slow_val = slow_sum / SLOW_PERIOD

        self.bars[index].sma_fast = fast_val
        self.bars[index].sma_slow = slow_val

        that_bar = self.bars[index]

        # print('calc_sma', index, that_bar.start_time, that_bar.px_open, that_bar.px_high, that_bar.px_low,
        #       that_bar.px_close, that_bar.volume, that_bar.sma_fast, that_bar.sma_slow)

    def get_bar_count(self):
        return len(self.bars)

    def check_signal(self, at_index):
        if len(self.bars) <= SLOW_PERIOD:
            print("not enough data")
            return

        if at_index <= SLOW_PERIOD:
            return

        last_bar_diff = self.bars[at_index-1].macd - self.bars[at_index-1].macd_signal
        this_bar_diff = self.bars[at_index].macd - self.bars[at_index].macd_signal
        print('check_signal_index {0} {1:.4f} {2:.4f}'.format(at_index, last_bar_diff, this_bar_diff))

        if last_bar_diff < 0 < this_bar_diff:
            # Target position is 1 unit
            print('cross up')

        if this_bar_diff < 0 < last_bar_diff:
            # Target position is -1 unit
            print('cross down')

        if this_bar_diff > 0:
            return 1
        else:
            return -1


class SignerConnector:
    def __init__(self, api_root):
        self.api_root = api_root

    def new_order(self, symbol, price, quantity, buy):
        url = "%s/newOrder" % self.api_root
        data = {'symbol': symbol, 'price': price, 'quantity': quantity, 'buy': buy}
        headers = {'Content-type': 'application/json'}
        return requests.post(url, json=data, headers=headers)

    def cancel(self, trxid):
        url = "%s/cancelOrder" % self.api_root
        data = {'transactionId': trxid}
        return requests.post(url, json=data)

    def cancel_all(self, symbol):
        url = "%s/cancelAll" % self.api_root
        data = {'symbol': symbol}
        return requests.post(url, json=data)


class OrderManager:

    def __init__(self, symbol):
        self.symbol = symbol
        self.orders = {}
        self.trades = {}
        self.buy_open = 0
        self.sell_open = 0
        self.pnl = 0
        self.position = 0
        self.size = 0.01
        self.last_price = 0.0
        self.signer = SignerConnector(api_root='http://127.0.0.1:8090/signer/v1')
        self.api_server = CybexRestful(api_root='http://210.3.74.58:58091/api/v1')


    def calculate_open_qty(self):
        self.buy_open = 0
        self.sell_open = 0
        for order in self.orders:
            if order.order_status in {OrderStatus.PendingNew, OrderStatus.New, OrderStatus.PartiallyFilled,
                                      OrderStatus.PendingCancel}:
                if order.sell_asset_id == sym_base:
                    # Add to pseudo sell
                    self.sell_open = self.sell_open + order.to_sell - order.sold
                if order.buy_asset_id == sym_base:
                    # Add to pseudo buy
                    self.buy_open = self.buy_open + order.to_receive - order.received

    def handle_signal(self, signal, orderbook):
        pseudo_pos = self.position + self.buy_open - self.sell_open
        target = self.size * signal

        pending_count = 0
        # Cancel open order if it is the opposite side of the target
        for order in self.orders:
            if order.order_status in {OrderStatus.PendingNew, OrderStatus.PendingCancel}:
                pending_count = pending_count + 1
            if order.order_status in {OrderStatus.PendingNew, OrderStatus.New, OrderStatus.PartiallyFilled}:
                if target > 0 and order.sell_asset_id == sym_base:
                    self.cancel(order.trx_id)
                    order.order_status = OrderStatus.PendingCancel
                elif target < 0 and order.buy_asset_id == sym_base:
                    self.cancel(order.trx_id)
                    order.order_status = OrderStatus.PendingCancel

        if pending_count > 3:
            print('too many pending, retry next round')
            return

        # Assume pending cancel can be cancelled.
        # Calculate pseudo_pos again
        self.calculate_open_qty()
        pseudo_pos = self.position + self.buy_open - self.sell_open

        if target == pseudo_pos:
            # Check open orders, if the price had moved away, replace them.

            pass

        to_trade = target - pseudo_pos

        if to_trade * target < 0:
            # Opposite to_trade and target direction. Something wired happened, cancel all and retry later.
        if to_trade > 0:
            if target < 0:
                # Wanted to buy but target is negative. There are extra sell orders out there.
                # Cancel them all and pick up new data in the next cycle and process later.

                return
            best_ask = orderbook.get_best_ask()
            self.buy(to_trade, best_ask)
        elif to_trade < 0:
            best_bid = orderbook.get_best_bid()
            self.sell(-1 * to_trade, best_bid)


    def check_if_cancel(self, target):
        if target > 0:
            # Cancel all the sell orders

            # Cancel extra buy orders if any

        elif target < 0:
            # Cancel all the buy orders

            # Cancel extra sell orders if any

    @staticmethod
    def parse_order_signer(order_data):
        Order o = Order()
        o.buy_asset_id = order_data['minToReceive']['assetID']
        o.to_receive = order_data['minToReceive']['amount']
        o.sell_asset_id = order_data['amountToSell']['assetID']
        o.to_sell = order_data['amountToSell']['amount']
        o.trx_id = order_data['transactionId']
        o.order_status = None
        return o

    @staticmethod
    def parse_order_apiserver(order_data):
        Order o = Order()
        o.trx_id = order_data['transactionId']

        order_status_str = order_data['orderStatus']

        # order status parsing sequence same as sbe definition
        if order_status_str  == 'PENDING_NEW':
            o.order_status = OrderStatus.PendingNew
        elif order_status_str == 'OPEN':
            o.order_status = OrderStatus.New
        elif order_status_str == 'PENDING_CXL':
            o.order_status = OrderStatus.PendingCancel
        elif order_status_str == 'CANCELED':
            o.order_status = OrderStatus.Canceled
        elif order_status_str == 'FILLED':
            o.order_status = OrderStatus.Filled
        elif order_status_str == 'REJECTED':
            o.order_status = OrderStatus.Rejected

        o.order_sequence = order_data['orderSequence']

        o.sold = order_data['sold']
        o.received = order_data['received']

        return o


    def update_orders(self):
        order_jsons = self.api_server.get_orders()
        for order_json in order_jsons:
            order_update = OrderManager.parse_order_apiserver(order_json)

            if not order_update.trx_id in self.orders:
                print('Unrecognized order {0}'.format(order_update.trx_id))
                continue

            if order_update.order_status == OrderStatus.Rejected:
                remark = order_json['remark']
                print('Order {0} rejected. Reason : {1}'.format(order_update.trx_id, remark))
                self.orders.pop(order_update.trx_id, None)
                continue

            if order_update.order_status in {OrderStatus.PartiallyFilled, OrderStatus.Filled}:
                # Change filled quantity


            order = self.orders[order_update.trx_id]
            # use order to compare to order_update
            order.order_status =

        self.calculate_open_qty()

    def sell(self, price, quantity):
        print("sell", quantity)
        new_order_json = self.signer.new_order(self.symbol, price, quantity, False)
        new_order = self.parse_order_signer(new_order_json)
        # replace asset id with symbol
        new_order.sell_asset_id = sym_base
        new_order.buy_asset_id = sym_quote
        self.orders[new_order.trx_id] = new_order
        self.api_server.place_order(new_order_json)

    def buy(self, price, quantity):
        print("buy", quantity)
        new_order_json = self.signer.new_order(self.symbol, price, quantity, True)
        new_order = self.parse_order(new_order_json)
        # replace asset id with symbol
        new_order.sell_asset_id = sym_quote
        new_order.buy_asset_id = sym_base
        self.orders[new_order.trx_id] = new_order
        self.api_server.place_order(new_order_json)

    def cancel(self, trx_id):
        cancel = self.signer.cancel(trx_id)
        self.api_server.cancel_order(cancel)

def process_binance_data(mdb, start, end):
    results = binance_api.get_kline("BTCUSDT", start, end)
    for bar_data in results:
        bar = BarData()
        bar.start_time = datetime.fromtimestamp(bar_data[0]/1000.0)
        bar.px_open = float(bar_data[1])
        bar.px_high = float(bar_data[2])
        bar.px_low = float(bar_data[3])
        bar.px_close = float(bar_data[4])
        bar.volume = float(bar_data[5])
        bar.end_time = datetime.fromtimestamp(bar_data[0]/1000.0)

        mdb.update_bar_data(bar)

        print(bar.start_time, bar.px_open, bar.px_high, bar.px_low, bar.px_close, bar.volume)


def process_huobi_data(mdb, start, end):
    try:
        datas = huobi_api.get_ohlcv(symbol, start, end)
        for bar_data in datas:
            bar = BarData()
            bar.start_time = datetime.fromtimestamp(bar_data[0]/1000.0)
            bar.px_open = float(bar_data[1])
            bar.px_high = float(bar_data[2])
            bar.px_low = float(bar_data[3])
            bar.px_close = float(bar_data[4])
            bar.volume = float(bar_data[5])

            mdb.update_bar_data(bar)

            # print(bar.start_time, bar.px_open, bar.px_high, bar.px_low, bar.px_close, bar.volume)
        # print('got', len(results), 'bars', results)

        order_book = huobi_api.get_order_book(symbol)

        mdb.order_book.bids = order_book['bids']
        mdb.order_book.asks = order_book['asks']
        print('{0:.3f} {1:.3f}'.format(best_bid, best_ask))

    except requests.exceptions.HTTPError:
        print('http error, no matter, do it next time')


def do_signer_test():
    signer = SignerConnector('http://127.0.0.1:8090')
    # result = signer.new_order('ETH/USDT', 0.01, 0.004, True)
    result = signer.cancel('3d9aae07efe89b6ddcd1ab1e74c311024b541fa3')
    print(result.json())


if __name__ == '__main__':

    do_signer_test()

    config = configparser.ConfigParser()
    config.read('config.ini')

    binance_api = BinanceRestful(key=config['Binance']['key'], secret=config['Binance']['secret'])

    # result = binance_api.get_exchange_info()
    # print(result)

    huobi_api = HuobiApi(key=config['Huobi']['key'], secret=config['Huobi']['secret'])

    seller_id = ''

    mdb = MarketDataManager()
    om = OrderManager(seller_id)

    now = int(time())
    start = (now - 60 * 1000) * 1000
    end = now * 1000
    print("init data", start, end)

    # process_binance_data(mdb, start, end)
    process_huobi_data(mdb, start, end)
    mdb.redo_ema()

    while True:
        now = int(time())
        start = (now - 120) * 1000
        end = now * 1000

        # process_binance_data(mdb, start, end)
        process_huobi_data(mdb, start, end)
        bar_count = mdb.get_bar_count()

        # bar_count - 1 is the current bar
        mdb.calc_ema(bar_count - 2)
        mdb.calc_ema(bar_count - 1)

        signal = mdb.check_signal(bar_count - 2)
        om.update_orders()
        om.handle_signal(signal, mdb.get_order_book())

        sleep(3)


