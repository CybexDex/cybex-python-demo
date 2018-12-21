import os
import configparser
import requests
import sys
from datetime import datetime
from time import sleep, time
from binanceapi import BinanceRestful
from huobiapi import HuobiApi
from ordermanager import OrderManager, MarketDataManager, BarData
import threading


sym_base = 'ETH'
sym_quote = 'USDT'
symbol = 'ETH/USDT'

mdb = None
om = None


def input_thread():
    while True:
        cmd = input()
        print(datetime.now(), 'Got a command', cmd)
        if cmd == '+':
            om.buy_one(mdb.get_order_book())
        elif cmd == '-':
            om.sell_one(mdb.get_order_book())


thread = threading.Thread(target=input_thread)
thread.daemon = True
thread.start()


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
        # start_time = timer()
        data = huobi_api.get_ohlcv(symbol, start, end)
        order_book = huobi_api.get_order_book(symbol)
        # end_time = timer()
        # print(end_time - start_time)
        # Usually this takes 3.9 seconds

        for bar_data in data:
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

        mdb.order_book.bids = order_book['bids']
        mdb.order_book.asks = order_book['asks']

        mdb.best_bid = mdb.order_book.bids[0][0]
        mdb.best_ask = mdb.order_book.asks[0][0]

        # print('{0:.3f} {1:.3f}'.format(mdb.best_bid, mdb.best_ask))

    except requests.exceptions.HTTPError:
        print('http error, no matter, do it next time')
    except Exception:
        print('Unable to get data', sys.exc_info()[0])


if __name__ == '__main__':

    if not os.path.exists('config.ini'):
        print('need to have config.ini')
        exit(-1)

    config = configparser.ConfigParser()
    config.read('config.ini')

    # binance_api = BinanceRestful(key=config['Binance']['key'], secret=config['Binance']['secret'])
    # result = binance_api.get_exchange_info()
    # print(result)
    try:
        huobi_api = HuobiApi(key=config['Huobi']['key'], secret=config['Huobi']['secret'])
    except Exception:
        print('need to have huobi api key and secret in the config_uat.ini')
        exit(-1)

    try:
        account = config['Cybex']['account']
    except Exception:
        print('need to have cybex account setting in the config_uat.ini')
        exit(-1)

    mdb = MarketDataManager()
    om = OrderManager(account, symbol)

    # om.do_test_order()

    now = int(time())
    start = (now - 60 * 1000) * 1000
    end = now * 1000
    print(datetime.now(), "init data", start, end)

    # process_binance_data(mdb, start, end)
    process_huobi_data(mdb, start, end)
    mdb.redo_ema()

    signal_slots = {}

    while True:
        # calculate how much historical data need to be requested
        now = datetime.now()

        # calculate a few time related number
        now_s = int(time())
        start_s = (now_s - 120) * 1000
        end_s = now_s * 1000
        now_m = int(now_s / 60)

        # Get market data udpates
        process_huobi_data(mdb, start_s, end_s)
        bar_count = mdb.get_bar_count()

        # bar_count - 1 is the current bar
        mdb.calc_ema(bar_count - 2)
        mdb.calc_ema(bar_count - 1)

        om.update_orders()
        om.cancel_old_orders()

        current_pnl = om.calculate_pnl(mdb.get_order_book())

        pnl_changed = False
        pnl_change = abs(current_pnl - om.pnl)
        if pnl_change > 1:
            pnl_changed = True

        if pnl_changed:
            print("{0}, pnl changed {1}, cur pos, {2}".format(datetime.now(), current_pnl, om.position))
            om.pnl = current_pnl

        # Add 2 seconds delay for signal checking to allow all data to come in.
        cut_off = now_m * 60 + 3

        # print('now', now, 'now_m', now_m, 'now_s', now_s, 'cut_off', cut_off)

        if now_m not in signal_slots and now_s > cut_off:
            # If there is no action in this time slot, calculate to_trade and send order
            signal = mdb.check_signal(bar_count - 2)

            print('{0}, signal for slot {1} is {2}, pos {3}, pnl {4}'
                  .format(datetime.now(), now_m, signal, om.position, current_pnl))
            try:
                result = om.handle_signal(signal, mdb.get_order_book())
                if result is not None or signal is None:
                    signal_slots[now_m] = signal
            except Exception as e:
                print('handle_signal encounter error', e)
