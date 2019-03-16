#!/usr/bin/python3

from romeapi.connect import Cybex
import json
import sys
import time
import argparse


def format_response(response):
    return json.dumps(response, indent=1)


def print_usage(prog):
    print(prog, "-n <account name> -p <password> or -n <account name> -k <private key>")
    sys.exit(0)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--account_name", help="Account Name")
    parser.add_argument("-k", "--private_key", help="Private Key")
    parser.add_argument("-p", "--password", help="Logon Password")
    args = parser.parse_args()

    if args.account_name:
        account_name = args.account_name
        if args.private_key:
            key = args.private_key
            cybex = Cybex(accountName=account_name, key=key, env='prod')
        elif args.password:
            password = args.password
            cybex = Cybex(accountName=account_name, password=password, env='prod')
        else:
            print_usage(sys.argv[0])
    else:
        print_usage(sys.argv[0])

    markets = cybex.load_markets()
    print('market:')
    print(format_response(markets))

    # get account position
    balance = cybex.fetch_balance()
    print('balance:')
    print(format_response(balance))

    # use ARENA.ETH/ARENA.USDT for CYBEX Trading Contest
    asset_pair = 'ETH/USDT'

    # fetch two levels
    order_book = cybex.fetch_order_book(asset_pair, 2)

    print(format_response(order_book))

    # fetch last 5-minute kline data
    # optional parameters (startTime,endTime,etc) can also be set in the last parameter
    klines = cybex.fetch_ohlcv(asset_pair, '1m', {'limit': 5})
    print('klines:', format_response(klines))

    order_transaction_id = None

    # NOTES:
    # Two orders are placed below (one buy order, one sell order)
    # The buy order is cancelled by transaction Id through the cancel_order API call.
    # The sell order is cancelled by the cancell_all API call.

    # place a buy order at level 2 price
    if len(order_book["bids"]) > 1:
        quantity = 0.01
        price = order_book["bids"][1][0]
        print('buy ', asset_pair, quantity, '@', price)
        order_transaction_id, result = cybex.create_limit_buy_order(asset_pair, quantity, price)
        print(result)

    # place a sell order at level 2 price
    if len(order_book["asks"]) > 1:
        quantity = 0.01
        price = order_book["asks"][1][0]
        print('sell', asset_pair, quantity, '@', price)
        # if you need order transaction id, you can do:
        # order_transaction_id, result = cybex.create_limit_sell_order(asset_pair, quantity, price)
        sell_order = cybex.create_limit_sell_order(asset_pair, quantity, price)
        print(sell_order)

    # The sample code for market orders is commented below:
    # market_buy = cybex.create_market_buy_order(asset_pair, 0.1)
    # print(market_buy)

    # market_sell = cybex.create_market_sell_order(asset_pair, 0.1)
    # print(market_sell)

    if order_transaction_id is not None:
        cancel_order = cybex.cancel_order(order_transaction_id)
        print(cancel_order)

    # cancel all orders
    cancel_all_order = cybex.cancel_all(asset_pair)
    print(cancel_all_order)




