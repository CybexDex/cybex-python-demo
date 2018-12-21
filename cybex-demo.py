from time import sleep
from cybexapi import SignerConnector, CybexRestful


if __name__ == '__main__':
    signer = SignerConnector(api_root="http://127.0.0.1:8090/signer/v1")
    api_server = CybexRestful(api_root="https://api.cybex.io/v1")

    # Prepare order message using the signer
    order_msg = signer.prepare_order_message(asset_pair='ETH/USDT', price=80, quantity=0.1, side='buy')

    trx_id = order_msg['transactionId']

    order_result = api_server.send_transaction(order_msg)

    # sleep 5 seconds
    sleep(10)

    # Try to can
    cancel_msg = signer.prepare_cancel_message(trx_id)

    cancel_result = api_server.send_transaction(cancel_msg)
