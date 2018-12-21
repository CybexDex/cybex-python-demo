import configparser
from time import sleep
from cybexapi import SignerConnector, CybexRestful


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config_uat.ini')

    signer = SignerConnector()
    api_server = CybexRestful()

    # Prepare order message using the signer
    order_msg = signer.prepare_order_message('ETH/USDT', 80, 0.1, 'buy')

    trx_id = order_msg['transactionId']

    order_result = api_server.send_transaction(order_msg)

    # sleep 5 seconds
    sleep(10)

    # Try to can
    cancel_msg = signer.prepare_cancel_message(trx_id)

    cancel_result = api_server.send_transaction(cancel_msg)
