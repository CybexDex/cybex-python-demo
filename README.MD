WELCOME TO Cybex Python API
============================

This is the python wrapper for Cybex API server and Transaction Signer.


Quick start
------------


First thing is download and run the signer.

Signer can be obtained from here https://github.com/CybexDex/cyb-signer

After signer is running, you can use SignerConnector to connect to it.

```python
signer = SignerConnector(api_root="http://127.0.0.1:8090/signer/v1")
```

Connect to the api server using CybexRestful object.

```python
api_server = CybexRestful(api_root="https://api.cybex.io/v1")
```

Give signer the needed information to prepare a signed transaction for the buy order.

```python
order_msg = signer.prepare_order_message(asset_pair='ETH/USDT', price=80, quantity=0.1, side='buy')
```

Send the order to the API server
```python
order_result = api_server.send_transaction(order_msg)
```

Prepare the cancel message using the signer.
```python
cancel_msg = signer.prepare_cancel_message(trx_id)
```

Send the cancel message to the API server at the same end point.
```python
cancel_result = api_server.send_transaction(cancel_msg)
```


Features
---------

cybexapi.py provides 2 wrappers. One wraps around the Cybex's Restful API server.
Cybex API server mainly provides API calls to send transaction, query position, query order, etc 

The other one wraps the Transaction Signer.
Transaction Signer provies 3 api calls to provide signature to new order, cancel and cancel all orders.  



Auto Trader
------------

There is also a sample (simple) strategy implemented inside autotrader.py. 
It looks at huobi's market data, calculate 1 minute MACD crossing signals. 
Whenever the MACD cross up, the auto-trader buys. 
Whenever the MACD corss down,the auto-trader sells.

This auto-trader will require a config.ini to contain API keys for the Huobi market 
data api.







