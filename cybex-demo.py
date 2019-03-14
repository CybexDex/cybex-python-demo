#!/usr/bin/python3

from cybexapi.connect import Cybex
import json
import sys


def format_response(response):
    return json.dumps(response, indent=1)


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("Usage: ", sys.argv[0], '<account name> <private_key>')
        sys.exit()

    account_name = sys.argv[1]
    key = sys.argv[2]

    cybex = Cybex(accountName=account_name, key=key, env='prod')

    markets = cybex.load_markets()
    print('market:')
    print(format_response(markets))

    balance = cybex.fetch_balance()
    print('balance:')
    print(format_response(balance))

    asset_pair = 'ETH/USDT'

    # fetch two levels
    order_book = cybex.fetch_order_book(asset_pair, 2)

    print(format_response(order_book))

    # place a buy order at level 2 price
    if len(order_book["bids"]) > 1:
        quantity = 0.01
        price = order_book["bids"][1][0]
        print('buy ', asset_pair, quantity, '@', price)
        buy_order = cybex.create_limit_buy_order(asset_pair, quantity, price)
        print(buy_order)

    # place a sell order at level 2 price
    if len(order_book["asks"]) > 1:
        quantity = 0.01
        price = order_book["asks"][1][0]
        print('sell', asset_pair, quantity, '@', price)
        sell_order = cybex.create_limit_sell_order(asset_pair, quantity, price)
        print(sell_order)

    # The sample code for market orders is commented below:
    # market_buy = cybex.create_market_buy_order(asset_pair, 0.1)
    # print(market_buy)

    # market_sell = cybex.create_market_sell_order(asset_pair, 0.1)
    # print(market_sell)

    # cancel all orders
    cancel_all_order = cybex.cancel_all(asset_pair)
    print(cancel_all_order)




