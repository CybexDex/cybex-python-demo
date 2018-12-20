import os
import configparser
import requests
import sys
from datetime import datetime
from time import sleep, time
from binanceapi import BinanceRestful
from huobiapi import HuobiApi
from ordermanager import OrderManager, MarketDataManager, BarData
from cybexapi import SignerConnector, CybexRestful


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config_uat.ini')

    # Send a order
    asset_pair = 'ETH/USDT'
    price = 90
    quantity = 0.1
    side = 'buy'

    singer = SignerConnector()
    api_server = CybexRestful()

    # Submit order information to the signer.
    # If successful, the result is the data object that is used to send to the api
    # If unsuccessful, the result contains error message
    order_data = singer.new_order(asset_pair, price, quantity, side).json()

    if 'Status' in order_data and order_data['Status'] == 'Failed':
        # Order error in singer
        print(order_data['Message'])
        exit(-1)

    trx_id = order_data['transactionId']

    result = api_server.send_transaction(order_data).json()
    if result['Status'] == 'Failed':
        print('Send order failed, code', result['Code'], 'reason', result['Message'])
        exit(-1)

    # sleep 5 seconds
    sleep(5)

    # Try to can
    cancel_data = singer.cancel(trx_id).json()

    result = api_server.send_transaction(cancel_data)
