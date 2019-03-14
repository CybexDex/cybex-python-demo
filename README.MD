WELCOME TO Cybex Python API Demo
============================

This is the python demo for using Cybex python API.


Quick Start
------------

Use `cybex_demo.py` as a quick start to using Cybex Python API.

Please prepare below information before using `cybex-demo.py`:

1. __Account Name__
1. __Private Key__

__Usage:__
```
python3 cybex-demo.py <account name> <private key>
e.g. python3 cybex-demo.py test_user 5JbxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxXd
```


Features
---------

`cybexapi_connector.py` provides 2 wrappers. 

One wraps around the Cybex's Restful API server.

Cybex API server mainly provides API calls to send transaction, query position, query order, etc 

The other one wraps the Transaction Signer.

Transaction Signer provies 3 api calls to provide signature to new order, cancel and cancel all orders.  



Auto Trader
------------

`autotrader.py` is a sample (simple) strategy implemented using python. 
It looks at huobi's market data, calculate 1 minute MACD crossing signals.
 
Whenever the MACD cross up, the auto-trader buys.
 
Whenever the MACD corss down,the auto-trader sells.

This auto-trader will require a config.ini to contain API keys for the Huobi market 
data api.







