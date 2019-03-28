import requests
import sys
from datetime import datetime
from time import time
from ordermanager import OrderManager, MarketDataManager, BarData
import threading

import ccxt
from romeapi import Cybex

sym_base = 'ETH'
sym_quote = 'USDT'
symbol = 'ETH/USDT'

ACCOUNTNAME = ''
PASSWORD = ''

mdb = None
om = None

def input_thread():
    while True:
        cmd = input()
        print(datetime.now(), 'Got a command', cmd)
        if cmd == '+':
            om. market_buy_one()
        elif cmd == '-':
            om.market_sell_one()


thread = threading.Thread(target=input_thread)
thread.daemon = True
thread.start()

def process_huobi_data(mdb, start, end):
    try:

        order_book = huobi_api.fetch_order_book(symbol, limit=10)
        mdb.order_book.set_orderbook(order_book)

        data = huobi_api.fetch_ohlcv(symbol, since=start)

        for bar_data in data:
            mdb.update_bar_data(BarData(bar_data))

    except requests.exceptions.HTTPError:
        print('http error, no matter, do it next time')
    except Exception:
        print('Unable to get data', sys.exc_info()[0])


if __name__ == '__main__':

    # no need for credentials
    huobi_api = ccxt.huobipro()
    # provide accountname/password,
    cybex = Cybex(accountName=ACCOUNTNAME, password=PASSWORD)

    mdb = MarketDataManager()
    om = OrderManager(cybex, symbol)

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
