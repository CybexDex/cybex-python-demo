import sys
import requests
from enum import Enum
from datetime import datetime, timedelta
from cybexapi_connector import SignerConnector, CybexRestful, CybexException

FAST_PERIOD = 12
SLOW_PERIOD = 26
SIGNAL_PERIOD = 9


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
        self.side = None
        self.assetPair = None
        self.quantity = 0
        self.price = 0
        self.filled = 0
        self.avg_price = 0
        self.trx_id = ''
        self.timestamp = datetime.utcnow()


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
            return self.bids[0][0]
        return None

    def get_best_ask(self):
        if len(self.asks) > 0:
            return self.asks[0][0]
        return None

    def get_cur_px(self):
        if len(self.bids) > 0 and len(self.asks) > 0:
            return (self.asks[0][0] + self.bids[0][0]) / 2

        return 0


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
        if self.is_new_bar(bar):
            self.bars.append(bar)
            # print('insert a bar, current length', len(self.bars))
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
        last_bar = self.bars[index - 1]

        fast_k = 2 / (FAST_PERIOD + 1)
        slow_k = 2 / (SLOW_PERIOD + 1)
        signal_k = 2 / (SIGNAL_PERIOD + 1)

        this_bar.ema_fast = (this_bar.px_close - last_bar.ema_fast) * fast_k + last_bar.ema_fast
        this_bar.ema_slow = (this_bar.px_close - last_bar.ema_slow) * slow_k + last_bar.ema_slow
        this_bar.macd = this_bar.ema_fast - this_bar.ema_slow
        this_bar.macd_signal = (this_bar.macd - last_bar.macd_signal) * signal_k + last_bar.macd_signal

        # print('calc_ema {0} {1:.4f} {2:.4f} {3:.4f} {4:.4f}'
        #       .format(index, this_bar.macd, this_bar.macd_signal, this_bar.ema_fast, this_bar.ema_slow))

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
            return None

        if at_index <= SLOW_PERIOD:
            return None

        last_bar_diff = self.bars[at_index - 1].macd - self.bars[at_index - 1].macd_signal
        this_bar_diff = self.bars[at_index].macd - self.bars[at_index].macd_signal
        print('{0}, check_signal_index {1}, last {2:.4f}, this {3:.4f}'.format(datetime.now(), at_index, last_bar_diff, this_bar_diff))

        if last_bar_diff < 0 < this_bar_diff:
            # Target position is 1 unit
            print('cross up')
            return 1

        if this_bar_diff < 0 < last_bar_diff:
            # Target position is -1 unit
            print('cross down')
            return -1

        return None

        # if this_bar_diff > 0:
        #     return 1
        # else:
        #     return -1


class OrderManager:

    def __init__(self, account, assetPair):
        self.account = account
        self.assetPair = assetPair
        self.sym_base = assetPair.split('/')[0]
        self.sym_quote = assetPair.split('/')[1]
        self.orders = {}
        self.trades = {}
        self.total_sell = 0
        self.total_buy = 0
        self.buy_open = 0
        self.sell_open = 0
        self.pnl = 0
        self.position = 0
        self.size = 0.5
        self.last_price = 0.0
        self.signer = SignerConnector()
        self.api_server = CybexRestful()

    def calculate_pnl(self, orderbook):
        total_pnl = 0
        cur_px = orderbook.get_cur_px()
        for trx_id, order in self.orders.items():
            if order.filled > 0:
                if order.side == 'sell':
                    pnl = (order.avg_price - cur_px) * order.filled
                    total_pnl = total_pnl + pnl
                elif order.side == 'buy':
                    pnl = (cur_px - order.avg_price) * order.filled
                    total_pnl = total_pnl + pnl

        return total_pnl

    def update_status(self):
        self.buy_open = 0
        self.sell_open = 0
        self.total_sell = 0
        self.total_buy = 0

        for trx_id, order in self.orders.items():
            if order.order_status in {OrderStatus.PendingNew, OrderStatus.New, OrderStatus.PartiallyFilled,
                                      OrderStatus.PendingCancel}:
                if order.side == 'sell':
                    # Add to pseudo sell
                    self.sell_open = self.sell_open + (order.quantity - order.filled)
                if order.side == 'buy':
                    # Add to pseudo buy
                    self.buy_open = self.buy_open + (order.quantity - order.filled)

            if order.filled > 0:
                if order.side == 'sell':
                    self.total_sell = self.total_sell + order.filled
                elif order.side == 'buy':
                    self.total_buy = self.total_buy + order.filled

        self.position = self.total_buy - self.total_sell

    def buy_one(self, orderbook):
        best_ask = orderbook.get_best_ask()
        self.buy(best_ask+0.2, self.size)

    def sell_one(self, orderbook):
        best_bid = orderbook.get_best_bid()
        self.sell(best_bid-0.2, self.size)

    def handle_signal(self, signal, orderbook):
        if signal is None:
            return None

        target = self.size * signal

        pending_new_count = 0
        pending_count = 0
        # Cancel open order if it is the opposite side of the target
        for trx_id, order in self.orders.items():
            if not order.order_status:
                pending_new_count = pending_new_count + 1
            if order.order_status in {OrderStatus.PendingNew, OrderStatus.PendingCancel}:
                pending_count = pending_count + 1
            if order.order_status in {OrderStatus.PendingNew, OrderStatus.New, OrderStatus.PartiallyFilled}:
                if target > 0 and order.side == 'sell':
                    try:
                        self.cancel(order.trx_id)
                        order.order_status = OrderStatus.PendingCancel
                    except Exception as e:
                        print('cancel error', e)
                elif target < 0 and order.side == 'buy':
                    try:
                        self.cancel(order.trx_id)
                        order.order_status = OrderStatus.PendingCancel
                    except Exception as e:
                        print('cancel error', e)

        if pending_new_count > 1:
            raise CybexException('too many pending new, wait and retry next round')

        if pending_count > 3:
            raise CybexException('too many pending, wait and retry next round')

        # Assume pending cancel can be cancelled.
        # Calculate pseudo_pos again
        self.update_status()
        pseudo_pos = self.position + self.buy_open - self.sell_open

        to_trade = target - pseudo_pos

        print("{0}, current total_buy {1}, total_sell {2} buy_open {3}, sell_open {4}, position {5} pseudo_pos {6}, to_trade {7} "
              .format(datetime.now(), self.total_buy, self.total_sell, self.buy_open,
                      self.sell_open, self.position, pseudo_pos, to_trade))

        if target == pseudo_pos:
            return None

        # Now the target and to_trade is the same direction.
        if abs(to_trade) < 0.1:
            # to_trade too small, do nothing.
            return True

        if to_trade > 0:
            best_ask = orderbook.get_best_ask()
            self.buy(best_ask, to_trade)
            return True
        elif to_trade < 0:
            best_bid = orderbook.get_best_bid()
            self.sell(best_bid, -1 * to_trade)
            return True

    @staticmethod
    def parse_order_signer(order_data):
        o = Order()
        # o.buy_asset_id = order_data['minToReceive']['assetId']
        # o.to_receive = order_data['minToReceive']['amount']
        # o.sell_asset_id = order_data['amountToSell']['assetId']
        # o.to_sell = order_data['amountToSell']['amount']
        o.trx_id = order_data['transactionId']
        o.order_status = None
        return o

    @staticmethod
    def parse_order_apiserver(order_data):
        o = Order()
        o.trx_id = order_data['transactionId']

        order_status_str = order_data['orderStatus']

        # order status parsing sequence same as sbe definition
        if order_status_str == 'PENDING_NEW':
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

        o.filled = order_data['filledQuantity']
        o.avg_price = order_data['averagePrice']

        return o

    def update_orders(self):
        # noinspection PyBroadException
        try:
            order_datas = self.api_server.get_orders(self.account)

            for order_data in order_datas:
                order_update = OrderManager.parse_order_apiserver(order_data)

                if order_update.trx_id not in self.orders:
                    # print('Unrecognized order {0}'.format(order_update.trx_id))
                    continue

                if order_update.order_status == OrderStatus.Rejected:
                    remark = order_data['remark']
                    print('{0}, Order {1} rejected. Reason : {2}'.format(datetime.now(), order_update.trx_id, remark))
                    self.orders.pop(order_update.trx_id, None)
                    continue

                order = self.orders[order_update.trx_id]
                if order.order_status != order_update.order_status:
                    print('{0}, order status changed from {1} to {2}, trx_id {3}'
                          .format(datetime.now(), order.order_status, order_update.order_status, order.trx_id))

                # Filled quantity changed
                if order.filled != order_update.filled:
                    print('{0}, order filled change from {1} to {2}, avg_price {3}, order total qty {4}, trx_id {5}'
                          .format(datetime.now(), order.filled, order_update.filled,
                                  order_update.avg_price, order.quantity, order.trx_id))

                order.quantity = order_update.quantity
                order.avg_price = order_update.avg_price
                order.filled = order_update.filled
                order.order_status = order_update.order_status

            self.update_status()
        except Exception:
            print("unable to update orders:", sys.exc_info()[0])

    def cancel_old_orders(self):
        now = datetime.utcnow()
        for trx_id, order in self.orders.items():

            lapse = now - order.timestamp
            if lapse > timedelta(seconds=40) and order.order_status in {OrderStatus.New, OrderStatus.PartiallyFilled}:
                try:
                    self.cancel(order.trx_id)
                except Exception as e:
                    print('Cancel exception', e)

    def sell(self, price, quantity):
        quantity = round(quantity, 2)
        price = round(price, 2)
        new_order_msg = self.signer.prepare_order_message(self.assetPair, price, quantity, 'sell')
        new_order = self.parse_order_signer(new_order_msg)

        new_order.assetPair = self.assetPair
        new_order.quantity = quantity
        new_order.price = price
        new_order.side = 'sell'

        print(datetime.now(), "try to sell", new_order.quantity, "at", new_order.price, "trx_id", new_order.trx_id)

        result = self.api_server.send_transaction(new_order_msg)
        print('send order result:', result)

        self.orders[new_order.trx_id] = new_order

    def buy(self, price, quantity):
        quantity = round(quantity, 2)
        price = round(price, 2)
        new_order_msg = self.signer.prepare_order_message(self.assetPair, price, quantity, 'buy')
        new_order = self.parse_order_signer(new_order_msg)

        new_order.assetPair = self.assetPair
        new_order.quantity = quantity
        new_order.price = price
        new_order.side = 'buy'

        print(datetime.now(), "try to buy", new_order.quantity, "at", new_order.price, "trx_id", new_order.trx_id)

        result = self.api_server.send_transaction(new_order_msg)
        print('send order result:', result)

        self.orders[new_order.trx_id] = new_order

    def cancel(self, trx_id):
        print(datetime.now(), 'cancelling', trx_id)
        cancel = self.signer.prepare_cancel_message(trx_id)
        result = self.api_server.send_transaction(cancel)
        print('cancel result', result)

    def cancel_all(self, symbol):
        print(datetime.now(), 'cancelling all')
        cancel_all = self.signer.prepare_cancel_all_message(symbol)
        result = self.api_server.send_transaction(cancel_all)
        print('cancel all result', result)

    def do_test_order(self):
        self.buy(50, 1)